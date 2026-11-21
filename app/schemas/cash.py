from pydantic import BaseModel
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlmodel import Field

from app.models.cash import EntryType

class CashEntryCreate(BaseModel):
    type: EntryType
    amount: Decimal = Field(gt=0)
    description: str = Field(min_length=3)


class CashEntryRead(BaseModel):
    id: int 
    type: EntryType
    source: str
    sale_id: int
    description: str
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

class BalanceRead(BaseModel): 
    total_in: Decimal
    total_out: Decimal
    balance: Decimal

class ReportRow(BaseModel):
    period: str
    total_in: Decimal
    total_out: Decimal
    balance: Decimal

class ReportRead(BaseModel):
    start: date | None
    end: date | None
    group_by: str
    rows: list[ReportRow]