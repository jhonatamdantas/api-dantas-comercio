from sqlmodel import Session, select, desc
from app.models.fiado import FiadoPayment
from app.schemas.fiado import FiadoPaymentCreate, StatementRead
from app.models.sale import PaymentMethod, Sale
from app.models.client import Client
from fastapi import HTTPException
from app.services import cash_service
from app.models.cash import EntryType

def register_payment(session: Session, data: FiadoPaymentCreate) -> FiadoPayment:
    # 1. TODO: busque o cliente (404 se não existir)
    client = session.get(Client, data.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não existe")
    # 2. TODO: se data.payment_method == PaymentMethod.credit -> 400
    if data.payment_method == PaymentMethod.credit:
        raise HTTPException(status_code=404, detail="Erro ao pagar")
    #          (não faz sentido pagar fiado com fiado)
    # 3. TODO: se data.amount > client.pending_value -> 400 "Valor maior que a dívida"
    if data.amount > client.pending_value: #type: ignore
        raise HTTPException(status_code=404, detail="Valor maior que a dívida")
    # 4. TODO: client.pending_value -= data.amount
    client.pending_value -= data.amount #type: ignore

    # 5. TODO: crie o FiadoPayment com os dados e faça session.add
    fiado_payment = FiadoPayment(client_id=data.client_id, amount=data.amount, payment_method=data.payment_method)
    session.add(fiado_payment)


    # 6. TODO: cash_service.register_entry com ENTRADA,
    #          source="pagamento_fiado" e uma description citando o cliente
    inflow = EntryType.inflow
    cash_service.register_entry(type=inflow, session=session, amount=data.amount, source="pagamento_fiado")

    # 7. TODO: commit único, refresh do pagamento e return
    session.commit()
    session.refresh(fiado_payment)
    return fiado_payment


def get_statement(session: Session, client_id: int) -> StatementRead:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não existe")   
    
    # 2. TODO: select(Sale).where(Sale.client_id == client_id,
    #          Sale.payment_method == PaymentMethod.credit), ordenado por created_at desc
    statement = select(Sale).where(Sale.client_id == client_id, 
                              Sale.payment_method == PaymentMethod.credit).order_by(Sale.created_at.desc()) #type: ignore
    sales = session.exec(statement).all()

    # 3. TODO: select(FiadoPayment) do cliente, também por created_at desc
    fiado_payment = select(FiadoPayment).where(FiadoPayment.client_id == client_id).order_by(FiadoPayment.created_at.desc()) #type: ignore
    payments = session.exec(fiado_payment).all()

    # 4. TODO: monte e retorne o StatementRead com o pending_value atual
    return StatementRead(
        client_id=client_id, 
        pending_value=client.pending_value, 
        sales=sales, payments=payments) #type: ignore
