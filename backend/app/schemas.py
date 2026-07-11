from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime
from .models import RoleEnum, TransactionType


# ---------- Auth ----------
class UserCreate(BaseModel):
    business_name: str
    email: EmailStr
    password: str
    role: Optional[RoleEnum] = RoleEnum.smb_client
    preferred_language: Optional[str] = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    business_name: str
    email: EmailStr
    role: RoleEnum
    preferred_language: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Accounts ----------
class AccountOut(BaseModel):
    id: int
    account_number: str
    balance: float
    account_type: str

    class Config:
        from_attributes = True


class DepositWithdraw(BaseModel):
    account_id: int
    amount: float
    category: Optional[str] = "general"
    description: Optional[str] = ""


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_number: str
    amount: float
    description: Optional[str] = ""


# ---------- Transactions ----------
class TransactionOut(BaseModel):
    id: int
    account_id: int
    type: TransactionType
    amount: float
    category: str
    description: str
    counterparty_account: Optional[str]
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Compliance ----------
class ComplianceAlertOut(BaseModel):
    id: int
    transaction_id: int
    reason: str
    severity: str
    resolved: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------- Assistant ----------
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    reply: str
    language: str
