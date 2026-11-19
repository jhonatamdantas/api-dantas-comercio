from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session

from app.models.client import Client
from app.schemas.clients import ClientCreate, ClientUpdate, ClientRead

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("/", response_model=ClientRead, status_code=201)
def create_data(data: ClientCreate, session: Session = Depends(get_session)):
    client = Client.model_validate(data)
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.get("/", response_model=list[ClientRead])
def list_clients( 
    q: str | None = None, skip: int = 0, limit: int = Query(20, le=100),session: Session = Depends(get_session),):
    clients = select(Client).where(Client.active == True)
    if q:
        clients = select(Client).where(Client.name.ilike(f"%{q}%")) #type: ignore
    
    clients.offset(skip).limit(limit)
    return session.exec(clients).all()
    

@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, session: Session = Depends(get_session)): 
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(404, detail="Cliente não encontrado")
    return {"Cliente": client}


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, data: ClientUpdate, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(404, detail="Cliente não existe para ser atualizado")
    
    field = data.model_dump(exclude_unset=True)
    client.sqlmodel_update(field)

    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def deactivate_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)

    if client is None: 
        raise HTTPException(404, detail="Cliente não existe para ser desativado") 
    elif client.pending_value > 0:
        raise HTTPException(404, detail="Cliente possui saldo devedor") 
    
    session.delete(client)
    session.commit()
    return {"Status": "Cliente desativado com sucesso"}
