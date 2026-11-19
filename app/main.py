from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from app.db.session import create_table
from app.deps import get_current_user, require_owner

from app.routers import clients, products, sale, fiado, cash, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield

app = FastAPI(title="Dantas Comércio", lifespan=lifespan)

@app.get("/saude")
def saude():
    return {"status": "ok"}

app.include_router(clients.router, dependencies=[Depends(get_current_user)])
app.include_router(products.router, dependencies=[Depends(get_current_user)])
app.include_router(sale.router, dependencies=[Depends(get_current_user)])
app.include_router(fiado.router, dependencies=[Depends(get_current_user)])
app.include_router(cash.router, dependencies=[Depends(require_owner)])
app.include_router(auth.router)