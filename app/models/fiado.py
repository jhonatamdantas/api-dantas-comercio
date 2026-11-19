from sqlmodel import SQLModel, Field
from decimal import Decimal
from app.models.sale import PaymentMethod
from datetime import datetime, timezone


class FiadoPayment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    amount: Decimal
    payment_method: PaymentMethod
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))