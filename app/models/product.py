from decimal import Decimal
from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: Decimal = Field(default=0)
    stock: int = Field(default=0)
    min_stock: int = Field(default=0)
    active: bool = Field(default=True)