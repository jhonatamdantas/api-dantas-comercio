from sqlmodel import Session, select
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.models.user import User
from app.db.session import get_session
from app.schemas.auth import UserCreate, UserRead, Token
from app.deps import get_current_user, require_owner
from app.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not verify_password(form.password, user.hashed_password) or not user.active:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token(str(user.id))
    return Token(access_token=token, token_type="bearer")

@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user

@router.post("/users", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_owner),
):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email já existe")
    user = User(email=data.email,hashed_password=hash_password(data.password), role=data.role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user