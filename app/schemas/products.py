from pydantic import Field, BaseModel
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str = Field(max_length=150)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    min_stock: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: None | str = Field(default= None, max_length=150)
    price: None | Decimal = None
    stock: None | int = None
    min_stock: None | int = None


class ProductRead(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int
    min_stock: int
    active: bool
    model_config = {"from_attributes": True}
