from sqlmodel import Session, select, desc
from app.models.fiado import FiadoPayment
from app.schemas.fiado import FiadoPaymentCreate, StatementRead
from app.models.sale import PaymentMethod, Sale
from app.models.client import Client
from fastapi import HTTPException
from app.services import cash_service
from app.models.cash import EntryType

def register_payment(session: Session, data: FiadoPaymentCreate) -> FiadoPayment:
    client = session.get(Client, data.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não existe")
    if data.payment_method == PaymentMethod.credit:
        raise HTTPException(status_code=404, detail="Erro ao pagar")
    if data.amount > client.pending_value: #type: ignore
        raise HTTPException(status_code=404, detail="Valor maior que a dívida")
    client.pending_value -= data.amount #type: ignore

    fiado_payment = FiadoPayment(client_id=data.client_id, amount=data.amount, payment_method=data.payment_method)
    session.add(fiado_payment)


    inflow = EntryType.inflow
    cash_service.register_entry(type=inflow, session=session, amount=data.amount, source="pagamento_fiado")

    session.commit()
    session.refresh(fiado_payment)
    return fiado_payment


def get_statement(session: Session, client_id: int) -> StatementRead:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não existe")   
    
    statement = select(Sale).where(Sale.client_id == client_id, 
                              Sale.payment_method == PaymentMethod.credit).order_by(Sale.created_at.desc()) #type: ignore
    sales = session.exec(statement).all()

    fiado_payment = select(FiadoPayment).where(FiadoPayment.client_id == client_id).order_by(FiadoPayment.created_at.desc()) #type: ignore
    payments = session.exec(fiado_payment).all()

    return StatementRead(
        client_id=client_id, 
        pending_value=client.pending_value, 
        sales=sales, payments=payments) #type: ignore
