from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

from app.operations import OperationType


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


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
    created_at: Optional[str]

    class Config:
        from_attributes = True
