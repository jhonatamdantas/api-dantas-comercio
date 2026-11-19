from sqlmodel import Session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User, Role
from app.db.session import get_session
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(401, headers={"WWW-Authenticate": "Bearer"})
    user = session.get(User, int(subject))
    if user is None or not user.active:
        raise HTTPException(401, headers={"WWW-Authenticate": "Bearer"})
    return user

def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.owner:
        raise HTTPException(403, "Apenas o dono pode acessar")
    return user