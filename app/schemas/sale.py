from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.sale import PaymentMethod
from datetime import datetime

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class SaleCreate(BaseModel):
    client_id: int | None = None
    payment_method: PaymentMethod
    items: list[SaleItemCreate] = Field(min_length=1)

class SaleItemRead(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    model_config = {"from_attributes": True}

class SaleRead(BaseModel):
    client_id: int | None = None
    payment_method: PaymentMethod
    total: Decimal
    status: str
    created_at: datetime
    items: list[SaleItemRead]
    model_config = {"from_attributes": True}