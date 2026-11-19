from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class PaymentMethod(str, Enum):
    cash = "dinheiro"
    pix = "pix"
    card = "cartao"
    credit = "fiado"


class SaleStatus(str, Enum):
    completed = "concluida"
    canceled = "cancelada"


class Sale(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int | None = Field(default=None, foreign_key="client.id")
    payment_method: PaymentMethod
    total: Decimal
    status: SaleStatus = Field(default=SaleStatus.completed)
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))
    items: list["ItemSale"] = Relationship(back_populates="sale")

class ItemSale(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sale_id: int | None = Field(default=None, foreign_key="sale.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price: Decimal
    sale: Sale | None = Relationship(back_populates="items")