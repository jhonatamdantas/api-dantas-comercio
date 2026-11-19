from sqlmodel import Session
from app.schemas.sale import SaleCreate
from app.models.sale import Sale, ItemSale, SaleStatus
from app.models.client import Client
from fastapi import HTTPException
from app.models.product import Product
from decimal import Decimal
from app.services import cash_service
from app.models.cash import EntryType, CashEntry
from app.models.sale import PaymentMethod

def register_sale(session: Session, data: SaleCreate) -> Sale:
    # TODO (antes do loop, junto da validação do cliente):
    #   se data.payment_method == PaymentMethod.credit e data.client_id for None
    #   -> 400 "Venda no fiado exige cliente"
    if data.payment_method == PaymentMethod.credit and data.client_id is None:
        raise HTTPException(status_code=400, detail="Venda no fiado exige cliente")
    

    # 1. Valida o cliente só se foi informado (venda de balcão pode não ter)
    if data.client_id is not None:
        client = session.get(Client, data.client_id)

        if not client:
            raise HTTPException(status_code=404, detail="Cliente não existe")
        if not client.active:
            raise HTTPException(status_code=400, detail="Cliente inativo")

    # 2. Agrupa itens repetidos somando as quantidades
    items: dict[int, int] = {}
    for item in data.items:
        # get devolve 0 se o produto ainda não estiver no dicionário
        items[item.product_id] = items.get(item.product_id, 0) + item.quantity

    # 3. Valida cada produto, baixa o estoque e monta os itens (sem salvar ainda)
    total = Decimal("0")
    sale_items: list[ItemSale] = []

    
    for product_id, quantity in items.items():
        product = session.get(Product, product_id)

        if not product:
            raise HTTPException(
                status_code=404, detail=f"Produto {product_id} não existe"
            )
        if not product.active:
            raise HTTPException(
                status_code=400, detail=f"Produto '{product.name}' inativo"
            )
        if product.stock < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente para '{product.name}'",
            )

        product.stock -= quantity

        # unit_price é o preço de 1 unidade, congelado no momento da venda
        sale_items.append(
            ItemSale(
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
            )
        )

        # O subtotal da linha (preço x quantidade) entra só no total
        total += product.price * quantity
    if data.payment_method == PaymentMethod.credit:
        if client.pending_value + total > client.credit_client:
            raise HTTPException(status_code=400, detail="Limite de fiado excedido")
        client.pending_value += total


    # 4. Cria a venda com o total e usa flush para gerar o sale.id sem confirmar
    sale = Sale(
        client_id=data.client_id,
        payment_method=data.payment_method,
        total=total,
    )
    session.add(sale)
    session.flush()

    # 5. Agora o id existe: liga os itens à venda
    for sale_item in sale_items:
        sale_item.sale_id = sale.id
        session.add(sale_item)

    # 6. Lança a entrada no caixa (sem commit dentro do service)
    if data.payment_method != PaymentMethod.credit:
        cash_service.register_entry(
            session,
            type=EntryType.inflow,
            amount=total,
            source="venda",
            sale_id=sale.id,
        )

    # 7. Commit único: ou tudo é salvo, ou nada
    session.commit()
    session.refresh(sale)
    return sale

def cancel_sale(session: Session, sale_id: int) -> Sale:
    sale = session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(404, detail="Venda não existe")
    if sale.status == SaleStatus.canceled:
        raise HTTPException(400, detail="Venda já cancelada")

    if sale.payment_method == PaymentMethod.credit:
        client = session.get(Client, sale.client_id)
        if client.pending_value < sale.total: #type: ignore
            raise HTTPException(status_code=400, detail="Cliente já pagou parte da dívida, não é possível cancelar")

    for item in sale.items:
        product = session.get(Product, item.product_id)
        product.stock += item.quantity #type: ignore

    sale.status = SaleStatus.canceled
    
    if sale.payment_method == PaymentMethod.credit:
        client.pending_value -= sale.total #type: ignore
    else:
        cash_service.register_entry(
            session=session, 
            sale_id=sale_id, 
            amount=sale.total, 
            source="estorno_venda",
            type=EntryType.outflow)

    session.commit()
    session.refresh(sale)
    return sale