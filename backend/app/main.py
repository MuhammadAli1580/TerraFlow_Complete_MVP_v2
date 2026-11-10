import os, csv, io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db, ensure_columns
from .models import User, Workspace, Client, Quote, QuoteItem, Invoice, InvoiceItem, Expense, Payment
from .schemas import RegisterIn, LoginIn, ClientIn, QuoteIn, InvoiceIn, ExpenseIn, PaymentIn, WorkspaceIn
from .auth import hash_password, verify_password, create_token, current_user, current_workspace

Base.metadata.create_all(bind=engine)
ensure_columns()

app = FastAPI(title="TerraFlow API", version="1.1.0", description="TerraFlow business workflow SaaS MVP",
              docs_url=None if os.getenv("APP_ENV") == "production" else "/docs", redoc_url=None)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def client_check(db, client_id, workspace_id):
    client = db.query(Client).filter(Client.id == client_id, Client.workspace_id == workspace_id).first()
    if not client:
        raise HTTPException(404, "Client not found")
    return client

def next_number(db, model, workspace_id, prefix):
    count = db.query(model).filter(model.workspace_id == workspace_id).count() + 1
    return f"{prefix}-{date.today():%Y%m}-{count:04d}"

def quote_dict(q):
    return {"id":q.id,"number":q.number,"client_id":q.client_id,"status":q.status,
            "issue_date":q.issue_date.isoformat(),"expiry_date":q.expiry_date.isoformat() if q.expiry_date else None,
            "subtotal":float(q.subtotal),"vat_rate":float(q.vat_rate),"vat_amount":float(q.vat_amount),
            "total":float(q.total),"notes":q.notes,
            "items":[{"id":i.id,"description":i.description,"quantity":float(i.quantity),
                      "unit_price":float(i.unit_price),"line_total":float(i.line_total)} for i in q.items]}

def invoice_dict(i):
    return {"id":i.id,"number":i.number,"client_id":i.client_id,"quote_id":i.quote_id,"status":i.status,
            "issue_date":i.issue_date.isoformat(),"due_date":i.due_date.isoformat() if i.due_date else None,
            "subtotal":float(i.subtotal),"vat_rate":float(i.vat_rate),"vat_amount":float(i.vat_amount),
            "total":float(i.total),"amount_paid":float(i.amount_paid),"notes":i.notes,
            "items":[{"id":x.id,"description":x.description,"quantity":float(x.quantity),
                      "unit_price":float(x.unit_price),"line_total":float(x.line_total)} for x in i.items],
            "payments":[{"amount":float(p.amount),"payment_date":p.payment_date.isoformat(),"reference":p.reference} for p in i.payments]}

def workspace_dict(w):
    return {"id":w.id,"name":w.name,"currency":w.currency,"vat_registered":w.vat_registered,"vat_rate":float(w.vat_rate),
            **{k:(getattr(w,k) or "") for k in ("address","phone","email","vat_number","bank_name","account_number","branch_code")}}

@app.get("/health")
def health():
    return {"status":"ok","service":"TerraFlow API","version":"1.0.0"}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == data.email.lower()).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(email=data.email.lower(), full_name=data.full_name, password_hash=hash_password(data.password))
    db.add(user); db.flush()
    ws = Workspace(owner_id=user.id, name=data.workspace_name, currency="ZAR", country_code="ZA", vat_registered=False, vat_rate=15)
    db.add(ws); db.commit(); db.refresh(user); db.refresh(ws)
    return {"access_token":create_token(user),"token_type":"bearer","user":{"id":user.id,"email":user.email,"full_name":user.full_name},"workspace":{"id":ws.id,"name":ws.name}}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    ws = db.query(Workspace).filter(Workspace.owner_id == user.id).first()
    return {"access_token":create_token(user),"token_type":"bearer","user":{"id":user.id,"email":user.email,"full_name":user.full_name},"workspace":{"id":ws.id,"name":ws.name} if ws else None}

@app.get("/api/me")
def me(user: User = Depends(current_user), ws: Workspace = Depends(current_workspace)):
    return {"id":user.id,"email":user.email,"full_name":user.full_name,"workspace":workspace_dict(ws)}

@app.get("/api/clients")
def list_clients(db: Session=Depends(get_db), ws: Workspace=Depends(current_workspace)):
    return [vars_client(c) for c in db.query(Client).filter_by(workspace_id=ws.id).order_by(Client.created_at.desc()).all()]

def vars_client(c):
    return {"id":c.id,"name":c.name,"email":c.email,"phone":c.phone,"company_name":c.company_name,"billing_address":c.billing_address,"notes":c.notes}

@app.post("/api/clients")
def create_client(data: ClientIn, db: Session=Depends(get_db), ws: Workspace=Depends(current_workspace)):
    c=Client(workspace_id=ws.id,**data.model_dump()); db.add(c); db.commit(); db.refresh(c); return vars_client(c)

@app.put("/api/clients/{client_id}")
def update_client(client_id:int,data:ClientIn,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    c=client_check(db,client_id,ws.id)
    for k,v in data.model_dump().items(): setattr(c,k,v)
    db.commit(); db.refresh(c); return vars_client(c)

@app.delete("/api/clients/{client_id}")
def delete_client(client_id:int,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    c=client_check(db,client_id,ws.id)
    if db.query(Quote).filter_by(client_id=c.id).first() or db.query(Invoice).filter_by(client_id=c.id).first():
        raise HTTPException(409,"Client has financial records. Archive functionality should be used instead of deletion.")
    db.delete(c); db.commit(); return {"ok":True}

@app.get("/api/quotes")
def list_quotes(db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    return [quote_dict(q) for q in db.query(Quote).filter_by(workspace_id=ws.id).order_by(Quote.created_at.desc()).all()]

@app.post("/api/quotes")
def create_quote(data:QuoteIn,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    client_check(db,data.client_id,ws.id)
    subtotal=money(sum(Decimal(str(x.quantity))*Decimal(str(x.unit_price)) for x in data.items))
    vat=money(subtotal*Decimal(str(data.vat_rate))/Decimal("100"))
    q=Quote(workspace_id=ws.id,client_id=data.client_id,number=next_number(db,Quote,ws.id,"TF-Q"),
            issue_date=data.issue_date,expiry_date=data.expiry_date,status="draft",subtotal=subtotal,
            vat_rate=data.vat_rate,vat_amount=vat,total=money(subtotal+vat),notes=data.notes)
    for x in data.items:
        q.items.append(QuoteItem(description=x.description,quantity=x.quantity,unit_price=x.unit_price,
                                 line_total=money(Decimal(str(x.quantity))*Decimal(str(x.unit_price)))))
    db.add(q); db.commit(); db.refresh(q); return quote_dict(q)

@app.patch("/api/quotes/{quote_id}/status")
def quote_status(quote_id:int,status:str,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    q=db.query(Quote).filter_by(id=quote_id,workspace_id=ws.id).first()
    if not q: raise HTTPException(404,"Quotation not found")
    if q.status in ("approved","rejected","cancelled"): raise HTTPException(409,"This quotation is already finalised")
    if status not in ("sent","approved","rejected","changes_requested","cancelled"): raise HTTPException(400,"Invalid status")
    q.status=status; db.commit(); return quote_dict(q)

@app.post("/api/quotes/{quote_id}/convert")
def convert_quote(quote_id:int,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    q=db.query(Quote).filter_by(id=quote_id,workspace_id=ws.id).first()
    if not q: raise HTTPException(404,"Quotation not found")
    if q.status != "approved": raise HTTPException(409,"Only approved quotations can be converted")
    existing=db.query(Invoice).filter_by(quote_id=q.id,workspace_id=ws.id).first()
    if existing: raise HTTPException(409,"An invoice already exists for this quotation")
    inv=Invoice(workspace_id=ws.id,client_id=q.client_id,quote_id=q.id,number=next_number(db,Invoice,ws.id,"TF-I"),
                status="draft",issue_date=date.today(),subtotal=q.subtotal,vat_rate=q.vat_rate,
                vat_amount=q.vat_amount,total=q.total,notes=q.notes)
    for it in q.items:
        inv.items.append(InvoiceItem(description=it.description,quantity=it.quantity,unit_price=it.unit_price,line_total=it.line_total))
    db.add(inv); db.commit(); db.refresh(inv); return invoice_dict(inv)

@app.get("/api/invoices")
def list_invoices(db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    return [invoice_dict(i) for i in db.query(Invoice).filter_by(workspace_id=ws.id).order_by(Invoice.created_at.desc()).all()]

@app.post("/api/invoices")
def create_invoice(data:InvoiceIn,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    client_check(db,data.client_id,ws.id)
    subtotal=money(sum(Decimal(str(x.quantity))*Decimal(str(x.unit_price)) for x in data.items))
    vat=money(subtotal*Decimal(str(data.vat_rate))/Decimal("100"))
    inv=Invoice(workspace_id=ws.id,client_id=data.client_id,number=next_number(db,Invoice,ws.id,"TF-I"),
                issue_date=data.issue_date,due_date=data.due_date,status="draft",subtotal=subtotal,
                vat_rate=data.vat_rate,vat_amount=vat,total=money(subtotal+vat),notes=data.notes)
    for x in data.items:
        inv.items.append(InvoiceItem(description=x.description,quantity=x.quantity,unit_price=x.unit_price,
                                     line_total=money(Decimal(str(x.quantity))*Decimal(str(x.unit_price)))))
    db.add(inv); db.commit(); db.refresh(inv); return invoice_dict(inv)

@app.patch("/api/invoices/{invoice_id}/status")
def invoice_status(invoice_id:int,status:str,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    inv=db.query(Invoice).filter_by(id=invoice_id,workspace_id=ws.id).first()
    if not inv: raise HTTPException(404,"Invoice not found")
    if status not in ("sent","cancelled"): raise HTTPException(400,"Use payment recording to mark an invoice paid")
    if status=="cancelled" and Decimal(str(inv.amount_paid))>0: raise HTTPException(409,"Invoices with payments cannot be voided")
    inv.status=status; db.commit(); return invoice_dict(inv)

@app.post("/api/invoices/{invoice_id}/payments")
def record_payment(invoice_id:int,data:PaymentIn,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    inv=db.query(Invoice).filter_by(id=invoice_id,workspace_id=ws.id).first()
    if not inv: raise HTTPException(404,"Invoice not found")
    if Decimal(str(inv.amount_paid))+Decimal(str(data.amount)) > Decimal(str(inv.total)):
        raise HTTPException(400,"Payment exceeds outstanding balance")
    p=Payment(workspace_id=ws.id,invoice_id=inv.id,amount=data.amount,payment_date=data.payment_date,reference=data.reference)
    db.add(p); inv.amount_paid=money(Decimal(str(inv.amount_paid))+Decimal(str(data.amount)))
    inv.status="paid" if inv.amount_paid >= inv.total else "partially_paid"
    db.commit(); db.refresh(inv); return invoice_dict(inv)

@app.get("/api/expenses")
def list_expenses(db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    rows=db.query(Expense).filter_by(workspace_id=ws.id).order_by(Expense.expense_date.desc()).all()
    return [{"id":e.id,"supplier":e.supplier,"description":e.description,"category":e.category,"expense_date":e.expense_date.isoformat(),"amount":float(e.amount),"vat_amount":float(e.vat_amount)} for e in rows]

@app.post("/api/expenses")
def create_expense(data:ExpenseIn,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    e=Expense(workspace_id=ws.id,**data.model_dump()); db.add(e); db.commit(); db.refresh(e)
    return {"id":e.id,"supplier":e.supplier,"description":e.description,"category":e.category,"expense_date":e.expense_date.isoformat(),"amount":float(e.amount),"vat_amount":float(e.vat_amount)}

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id:int,db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    e=db.query(Expense).filter_by(id=expense_id,workspace_id=ws.id).first()
    if not e: raise HTTPException(404,"Expense not found")
    db.delete(e); db.commit(); return {"ok":True}

@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    invoices=db.query(Invoice).filter_by(workspace_id=ws.id).all()
    quotes=db.query(Quote).filter_by(workspace_id=ws.id).all()
    expenses=db.query(Expense).filter_by(workspace_id=ws.id).all()
    revenue=sum(Decimal(str(i.amount_paid)) for i in invoices)
    outstanding=sum(max(Decimal("0"),Decimal(str(i.total))-Decimal(str(i.amount_paid))) for i in invoices if i.status not in ("cancelled",))
    expense_total=sum(Decimal(str(e.amount)) for e in expenses)
    return {"revenue":money(revenue),"outstanding":money(outstanding),"expenses":money(expense_total),
            "pending_approvals":sum(1 for q in quotes if q.status in ("sent","viewed")),
            "approved_quotes":sum(1 for q in quotes if q.status=="approved"),
            "clients":db.query(Client).filter_by(workspace_id=ws.id).count(),
            "quotes_count":len(quotes),"invoices_count":len(invoices)}

@app.get("/api/reports/summary.csv")
def report_csv(db:Session=Depends(get_db),ws:Workspace=Depends(current_workspace)):
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(["Type","Number/Description","Date","Status/Category","Amount ZAR"])
    for q in db.query(Quote).filter_by(workspace_id=ws.id).all():
        writer.writerow(["Quotation",q.number,q.issue_date,q.status,str(q.total)])
    for i in db.query(Invoice).filter_by(workspace_id=ws.id).all():
        writer.writerow(["Invoice",i.number,i.issue_date,i.status,str(i.total)])
    for e in db.query(Expense).filter_by(workspace_id=ws.id).all():
        writer.writerow(["Expense",e.description,e.expense_date,e.category,str(e.amount)])
    return Response(output.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=terraflow-report.csv"})


# ---------- v1.1: company profile, editing drafts ----------
@app.put("/api/workspace")
def update_workspace(data: WorkspaceIn, db: Session=Depends(get_db), ws: Workspace=Depends(current_workspace)):
    for k, v in data.model_dump().items(): setattr(ws, k, v)
    db.commit(); db.refresh(ws); return workspace_dict(ws)

def apply_totals(doc, items, vat_rate):
    subtotal = money(sum(Decimal(str(x.quantity))*Decimal(str(x.unit_price)) for x in items))
    vat = money(subtotal*Decimal(str(vat_rate))/Decimal("100"))
    doc.subtotal, doc.vat_rate, doc.vat_amount, doc.total = subtotal, vat_rate, vat, money(subtotal+vat)

def line(model, x):
    return model(description=x.description, quantity=x.quantity, unit_price=x.unit_price,
                 line_total=money(Decimal(str(x.quantity))*Decimal(str(x.unit_price))))

@app.put("/api/quotes/{quote_id}")
def update_quote(quote_id:int, data:QuoteIn, db:Session=Depends(get_db), ws:Workspace=Depends(current_workspace)):
    q = db.query(Quote).filter_by(id=quote_id, workspace_id=ws.id).first()
    if not q: raise HTTPException(404, "Quotation not found")
    if q.status != "draft": raise HTTPException(409, "Only draft quotations can be edited")
    client_check(db, data.client_id, ws.id)
    q.client_id, q.issue_date, q.expiry_date, q.notes = data.client_id, data.issue_date, data.expiry_date, data.notes
    apply_totals(q, data.items, data.vat_rate)
    q.items.clear()
    for x in data.items: q.items.append(line(QuoteItem, x))
    db.commit(); db.refresh(q); return quote_dict(q)

@app.put("/api/invoices/{invoice_id}")
def update_invoice(invoice_id:int, data:InvoiceIn, db:Session=Depends(get_db), ws:Workspace=Depends(current_workspace)):
    inv = db.query(Invoice).filter_by(id=invoice_id, workspace_id=ws.id).first()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status != "draft": raise HTTPException(409, "Only draft invoices can be edited")
    client_check(db, data.client_id, ws.id)
    inv.client_id, inv.issue_date, inv.due_date, inv.notes = data.client_id, data.issue_date, data.due_date, data.notes
    apply_totals(inv, data.items, data.vat_rate)
    inv.items.clear()
    for x in data.items: inv.items.append(line(InvoiceItem, x))
    db.commit(); db.refresh(inv); return invoice_dict(inv)
