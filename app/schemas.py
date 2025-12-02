from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict

from app.operations import OperationType


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(UserBase):
    id: int
    role: str
    model_config = ConfigDict(from_attributes=True)


class CalculationCreate(BaseModel):
    a: float
    b: float
    type: OperationType

    @model_validator(mode="after")
    def check_division_by_zero(self):
        if self.type == OperationType.Divide and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: OperationType
    result: Optional[float]
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    model_config = ConfigDict(from_attributes=True)


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshTokenRead(BaseModel):
    id: int
    revoked: bool
    created_at: Optional[datetime]
    expires_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class UserWithTokenCount(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    token_count: int
    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    role: str
    model_config = ConfigDict(from_attributes=True)
