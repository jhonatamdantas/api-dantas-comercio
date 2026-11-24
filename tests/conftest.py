import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import app.models  # registra as tabelas no metadata
from app.main import app
from app.db.session import get_session
from app.models.user import User, Role
from app.core.security import hash_password, create_access_token


@pytest.fixture
def engine():
    # Banco em memória: nasce e morre a cada teste
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # sem isso, cada conexão veria um banco vazio diferente
    )
    # TODO: crie as tabelas com SQLModel.metadata.create_all(engine)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    # Sessão do TESTE: serve para montar dados e conferir o resultado
    with Session(engine) as session:
        yield session


@pytest.fixture
def api(engine):
    def get_session_override():
        # TODO: abra uma Session(engine) NOVA com `with` e faça yield dela
        # (uma por requisição, igual à produção)
        with Session(engine) as session:
            yield session
        ...

    # TODO: app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)  # sem `with`: não roda o lifespan, que usaria o banco real
    # TODO: app.dependency_overrides.clear()
    app.dependency_overrides.clear()


def make_headers(session: Session, email: str, role: Role) -> dict:
    user = User(hashed_password=hash_password("senha1234"), role=role, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}
    # TODO: crie o User com hashed_password=hash_password("senha1234"), add, commit, refresh
    # TODO: token = create_access_token(str(user.id))
    # TODO: retorne {"Authorization": f"Bearer {token}"}
    ...


@pytest.fixture
def owner_headers(session):
    return make_headers(session, "dono@teste.com", Role.owner)


@pytest.fixture
def employee_headers(session):
    # TODO: o mesmo, com outro e-mail e Role.employee
    return make_headers(session, "dono_vip@teste.com", Role.employee)