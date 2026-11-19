from decimal import Decimal
from sqlmodel import SQLModel, Field

class Client(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    phone_number: str | None = Field(max_length=50)
    address: str | None = Field(max_length=150)
    credit_client: Decimal = Field(default=0)
    pending_value: Decimal = Field(default=0)
    active: bool = Field(default=True)