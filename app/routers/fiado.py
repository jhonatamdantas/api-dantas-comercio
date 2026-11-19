from fastapi import APIRouter, Depends
from app.schemas.fiado import FiadoPaymentRead, FiadoPaymentCreate, DebtorRead
from app.schemas.fiado import StatementRead
from sqlmodel import Session, select, desc
from app.db.session import get_session
from app.services import fiado_service
from app.models.client import Client


router = APIRouter(prefix="/fiado", tags=["Fiado"])

@router.post("/payments", response_model=FiadoPaymentRead, status_code=201)
def pay(data: FiadoPaymentCreate, session: Session = Depends(get_session)):
    return fiado_service.register_payment(session, data)

@router.get("/debtors", response_model=list[DebtorRead])
def list_debtors(session: Session = Depends(get_session)):
    client = select(Client).where(Client.pending_value > 0, Client.active == True).order_by(Client.pending_value.desc()) #type: ignore
    return session.exec(client).all()

@router.get("/clients/{client_id}/statement", response_model=StatementRead)
def statement(client_id: int, session: Session = Depends(get_session)):
    return fiado_service.get_statement(session, client_id)