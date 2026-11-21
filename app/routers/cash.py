from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, desc

from app.db.session import get_session
from app.models.cash import CashEntry, EntryType
from app.schemas.cash import BalanceRead, CashEntryRead, CashEntryCreate, ReportRead
from app.services import cash_service

router = APIRouter(prefix="/cash", tags=["Cash"])


@router.post("/entries", response_model=CashEntryRead, status_code=201)
def create_entry(data: CashEntryCreate, session: Session = Depends(get_session)):
    return cash_service.register_manual_entry(session, data)


@router.get("/entries", response_model=list[CashEntryRead])
def list_entries(
    start: date | None = None,
    end: date | None = None,
    entry_type: EntryType | None = Query(default=None, alias="type"),  # alias evita sombrear o type do Python
    source: str | None = None,
    skip: int = 0,
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):

    if start and end:
        if start > end:
            raise HTTPException(400, detail="Horário de início acima do fim")
    start_dt, end_dt = cash_service.period_limits(start, end)
    query = select(CashEntry)
    if entry_type:
        query = query.where(CashEntry.type == entry_type)
    if source:
        query = query.where(CashEntry.source == source)
    start_dt, end_dt = cash_service.period_limits(start, end)
    if start_dt:
        query = query.where(CashEntry.created_at >= start_dt)
    if end_dt:
        query = query.where(CashEntry.created_at < end_dt)  

    query.order_by(desc(CashEntry.created_at)).offset(skip).limit(limit)
    return session.exec(query).all()


@router.get("/balance", response_model=BalanceRead)
def balance(
    start: date | None = None,
    end: date | None = None,
    session: Session = Depends(get_session),
):
    if start and end:
        if start > end:
            raise HTTPException(400, detail="Horário de início acima do fim")

    return cash_service.get_balance(session, start, end)

@router.get("/report", response_model=ReportRead)
def report(
    start: date | None = None,
    end: date | None = None,
    group_by: Literal["day", "month"] = "day",
    session: Session = Depends(get_session),
):
    if start and end:
        if start > end:
            raise HTTPException(400, detail="Horário de início acima do fim")
    return cash_service.get_report(session,start, end, group_by)