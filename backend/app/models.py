from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    workspace: Mapped["Workspace"] = relationship(back_populates="owner", uselist=False)

class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(160), default="My Workspace")
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    country_code: Mapped[str] = mapped_column(String(2), default="ZA")
    vat_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_rate: Mapped[float] = mapped_column(Numeric(5,2), default=15.00)
    address: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    vat_number: Mapped[str] = mapped_column(String(40), default="")
    bank_name: Mapped[str] = mapped_column(String(120), default="")
    account_number: Mapped[str] = mapped_column(String(60), default="")
    branch_code: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    owner: Mapped[User] = relationship(back_populates="workspace")

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    company_name: Mapped[str] = mapped_column(String(160), default="")
    billing_address: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    number: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    subtotal: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5,2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    items: Mapped[list["QuoteItem"]] = relationship(cascade="all, delete-orphan")

class QuoteItem(Base):
    __tablename__ = "quote_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Numeric(12,3), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    line_total: Mapped[float] = mapped_column(Numeric(14,2), default=0)

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    quote_id: Mapped[int | None] = mapped_column(ForeignKey("quotes.id"), nullable=True)
    number: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    subtotal: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5,2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    items: Mapped[list["InvoiceItem"]] = relationship(cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship()

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[float] = mapped_column(Numeric(12,3), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    line_total: Mapped[float] = mapped_column(Numeric(14,2), default=0)

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    supplier: Mapped[str] = mapped_column(String(160), default="")
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(80), default="Other")
    expense_date: Mapped[date] = mapped_column(Date, default=date.today)
    amount: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[float] = mapped_column(Numeric(14,2))
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    reference: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
