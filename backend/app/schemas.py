from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=160)
    workspace_name: str = Field(default="My Workspace", max_length=160)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ClientIn(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    company_name: str = ""
    billing_address: str = ""
    notes: str = ""

class ItemIn(BaseModel):
    description: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)

class QuoteIn(BaseModel):
    client_id: int
    issue_date: date
    expiry_date: date | None = None
    vat_rate: float = Field(default=0, ge=0, le=100)
    notes: str = ""
    items: list[ItemIn] = Field(min_length=1)

class InvoiceIn(BaseModel):
    client_id: int
    issue_date: date
    due_date: date | None = None
    vat_rate: float = Field(default=0, ge=0, le=100)
    notes: str = ""
    items: list[ItemIn] = Field(min_length=1)

class ExpenseIn(BaseModel):
    supplier: str = ""
    description: str
    category: str = "Other"
    expense_date: date
    amount: float = Field(gt=0)
    vat_amount: float = Field(default=0, ge=0)

class WorkspaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    address: str = ""
    phone: str = ""
    email: str = ""
    vat_number: str = ""
    bank_name: str = ""
    account_number: str = ""
    branch_code: str = ""

class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    payment_date: date
    reference: str = ""
