import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import app.models  
from app.main import app
from app.db.session import get_session
from app.models.user import User, Role
from app.core.security import hash_password, create_access_token

from decimal import Decimal

from app.models.client import Client     
from app.models.product import Product   


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def api(engine):
    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)  # sem `with`: não roda o lifespan, que usaria o banco real
    app.dependency_overrides.clear()


def make_headers(session: Session, email: str, role: Role) -> dict:
    user = User(hashed_password=hash_password("senha1234"), role=role, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def owner_headers(session):
    return make_headers(session, "dono@teste.com", Role.owner)


@pytest.fixture
def employee_headers(session):
    return make_headers(session, "dono_vip@teste.com", Role.employee)


@pytest.fixture
def product_a(session):
    product = Product(name="Arroz", price=Decimal("5.00"), stock=10)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture
def product_b(session):
    # Produto de R$ 20,00 com apenas 2 em estoque
    product = Product(name="Queijo", price=Decimal("20.00"), stock=2)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture
def maria(session):
    client = Client(name="Maria") # type:ignore
    session.add(client)
    session.commit()
    session.refresh(client)
    return client