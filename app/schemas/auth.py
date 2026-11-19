from pydantic import BaseModel, EmailStr
from sqlmodel import Field
from datetime import datetime, timezone

from app.models.user import Role

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role = Role.employee

class UserRead(BaseModel):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    role: Role = Field(default=Role.employee)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str