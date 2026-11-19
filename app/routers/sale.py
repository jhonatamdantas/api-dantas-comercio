from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleRead
from app.services import sale_service
from sqlmodel import desc

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SaleRead, status_code=201)
def create(data: SaleCreate, session: Session = Depends(get_session)):
    return sale_service.register_sale(session, data)


@router.get("/", response_model=list[SaleRead])
def list_sales(
    skip: int = 0,
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    sales = select(Sale).order_by(desc(Sale.created_at))
    sales.offset(skip).limit(limit)
    return session.exec(sales).all()


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(sale_id: int, session: Session = Depends(get_session)):
    sale = session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada")


@router.post("/{sale_id}/cancel", response_model=SaleRead)
def cancel(sale_id: int, session: Session = Depends(get_session)):
    return sale_service.cancel_sale(session, sale_id)