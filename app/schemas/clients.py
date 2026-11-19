from decimal import Decimal
from pydantic import BaseModel, Field

class ClientCreate(BaseModel):
    name: str = Field(min_length=2)
    phone_number: str = Field(max_length=50)
    address: str = Field(max_length=150)
    credit_client: Decimal = Field(ge=0, default=Decimal(0))

class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    phone_number: str | None = None
    address: str | None = None
    credit_client: Decimal | None = None

class ClientRead(BaseModel):
    id: int
    name: str
    phone_number: str
    pending_value: Decimal
    active: bool
    model_config = {"from_attributes": True}