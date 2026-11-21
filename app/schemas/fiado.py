from pydantic import Field, BaseModel
from decimal import Decimal
from datetime import datetime

from app.schemas.sale import SaleRead
from app.models.sale import PaymentMethod

class FiadoPaymentCreate(BaseModel):
    client_id: int
    amount : Decimal = Field(gt=0)
    payment_method: PaymentMethod

class FiadoPaymentRead(BaseModel):
    id: int
    client_id: int
    amount: Decimal
    payment_method: PaymentMethod
    created_at: datetime
    model_config = {"from_attributes": True}

class DebtorRead(BaseModel):
    id: int
    name: str
    phone_number: str
    pending_value: Decimal
    model_config = {"from_attributes": True}

class StatementRead(BaseModel):
    client_id: int
    pending_value: Decimal
    sales: list[SaleRead]          
    payments: list[FiadoPaymentRead]