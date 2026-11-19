from enum import Enum
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

class Role(str, Enum):
    owner = "dono"
    employee = "funcionario"

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: Role = Field(default=Role.employee)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))
