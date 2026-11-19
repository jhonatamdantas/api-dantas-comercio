from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlmodel import SQLModel, Field

class EntryType(str, Enum):
    inflow = "entrada"
    outflow = "saida"


class CashEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    type: EntryType
    amount: Decimal
    source: str 
    sale_id: int | None = Field(foreign_key="sale.id")
    description: str | None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))