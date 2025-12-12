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


class CalculationUpdate(BaseModel):
    """Schema for updating a calculation (PATCH/PUT)"""
    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[OperationType] = None

    @model_validator(mode="after")
    def check_division_by_zero(self):
        if self.type == OperationType.Divide and self.b is not None and self.b == 0:
            raise ValueError("Division by zero is not allowed")
        return self


class CalculationRead(BaseModel):
    id: int
    user_id: int
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


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class PasswordChangeRequest(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)

    @model_validator(mode="after")
    def passwords_different(self):
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self
