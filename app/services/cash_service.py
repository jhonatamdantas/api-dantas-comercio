from decimal import Decimal
from sqlmodel import Session, select, func
from app.models.cash import CashEntry, EntryType  # ajuste ao nome do seu model
from app.schemas.cash import CashEntryCreate,BalanceRead, ReportRead, ReportRow
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Belem")


def period_limits(start: date | None, end: date | None) -> tuple[datetime | None, datetime | None]:
    start_dt = None
    end_dt = None

    if start:
        start_dt = datetime.combine(start, time.min, tzinfo=LOCAL_TZ).astimezone(timezone.utc)
    if end:
        end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=LOCAL_TZ).astimezone(timezone.utc)

    return start_dt, end_dt


def register_entry(session: Session,type: EntryType,amount: Decimal,source: str,sale_id: int | None = None,description: str | None = None,) -> CashEntry:  
    cash_entry = CashEntry(
        sale_id=sale_id,
        description=description,
        amount=amount,
        type=type,
        source=source,
    )
    session.add(cash_entry)
    return cash_entry


def register_manual_entry(session: Session, data: CashEntryCreate) -> CashEntry:
    if data.type == EntryType.inflow:
        source = "entrada_avulsa"
    else:
        source = "despesa"
        
    cash_entry = register_entry(
        session=session,
        type=data.type,
        amount=data.amount,
        source=source,
        description=data.description,
    )
    session.commit()
    session.refresh(cash_entry)
    return cash_entry 

def get_balance(session: Session, start: date | None, end: date | None) -> BalanceRead:
    start_dt, end_dt = period_limits(start, end)
    def total_by_type(entry_type: EntryType) -> Decimal:
        query = select(func.sum(CashEntry.amount)).where(CashEntry.type == entry_type)
        if start_dt:
            query = query.where(CashEntry.created_at >= start_dt)
        if end_dt:
            query = query.where(CashEntry.created_at < end_dt)  
        result = session.exec(query).one()
        return result or Decimal("0")

    total_in = total_by_type(EntryType.inflow)
    total_out = total_by_type(EntryType.outflow)

    return BalanceRead(
        total_in=total_in,
        total_out=total_out,
        balance=total_in - total_out
    )


def get_report(session: Session, start: date | None, end: date | None, group_by: str) -> ReportRead:
    start_dt, end_dt = period_limits(start, end)
    query = select(CashEntry).order_by(CashEntry.created_at) #type: ignore
    if start_dt:
        query = query.where(CashEntry.created_at >= start_dt)
    if end_dt:
        query = query.where(CashEntry.created_at < end_dt)  
    entries = session.exec(query).all()
    date_format = "%Y-%m-%d" if group_by == "day" else "%Y-%m"

    totals: dict[str, dict[str, Decimal]] = {}
    for entry in entries:
        created = entry.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        key = created.astimezone(LOCAL_TZ).strftime(date_format)
        if key not in totals:
            totals[key] = {"in": Decimal("0"), "out": Decimal("0")}

        if entry.type == EntryType.inflow:
            totals[key]["in"] += entry.amount
        else:
            totals[key]["out"] += entry.amount

    rows = [
        ReportRow(
            period=key,
            total_in=values["in"],
            total_out=values["out"],
            balance=values["in"] - values["out"],
        ) 
        for key, values in sorted(totals.items())
    ]
    return ReportRead(start=start, end=end, group_by=group_by, rows=rows)
