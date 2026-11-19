from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.product import Product
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.post("/", response_model=ProductRead, status_code=201)
def create_data(data: ProductCreate, session: Session = Depends(get_session)):
    product = Product.model_validate(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/", response_model=list[ProductRead])
def list_product(
    q : str | None = None, skip: int = 0, limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    products = select(Product).where(Product.active == True)
    if q:
        products = select(Product).where(Product.name.ilike(f"%{q}%")) #type: ignore

    products.offset(skip).limit(limit)
    return session.exec(products).all()


@router.get("/estoque-baixo", response_model=list[ProductRead])
def low_stock(session: Session = Depends(get_session)):
    products_low_stock = select(Product).where(Product.stock <= Product.min_stock, Product.active == True)
    if products_low_stock is None:
        raise HTTPException(404, detail="Produto não encontrado")
    return session.exec(products_low_stock).all()


@router.get("/{product_id}", response_model=ProductRead)
def get_client(product_id: int, session: Session = Depends(get_session)): 
    product = select(Product).where(Product.id == product_id)
    if product is None:
        raise HTTPException(404, detail="Produto não encontrado")
    return session.exec(product)


@router.patch("/{product_id}", response_model=ProductRead)
def update_client(product_id: int, data: ProductUpdate, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(404, detail="Produto não existe para ser atualizado")
    
    field = data.model_dump(exclude_unset=True)
    product.sqlmodel_update(field)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{cliente_id}", status_code=204)
def deactivate_product(product_id: int, session: Session = Depends(get_session)):
    product = select(Product).where(product_id == Product.id)
    if product is None:
        raise HTTPException(404, detail="Produto não encontrado")
    session.delete(product)
    session.commit()
    return {"Status": "Produto desativado com sucesso"}