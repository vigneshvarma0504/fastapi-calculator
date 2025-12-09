from typing import Optional, List
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


class UserRead(UserBase):
    id: int
    role: str
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


class CalculationCreate(BaseModel):
    operation: str = Field(..., description="Operation type: add, sub, mul, or div")
    operands: List[float] = Field(..., min_length=2, description="List of operands (at least 2)")

    @model_validator(mode="after")
    def validate_operation_and_operands(self):
        # Validate operation is supported
        valid_operations = ["add", "sub", "mul", "div"]
        if self.operation.lower() not in valid_operations:
            raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
        
        # Validate operands length
        if len(self.operands) < 2:
            raise ValueError("At least 2 operands are required")
        
        # Check for division by zero
        if self.operation.lower() == "div" and any(op == 0 for op in self.operands[1:]):
            raise ValueError("Division by zero is not allowed")
        
        return self


class CalculationUpdate(BaseModel):
    """Schema for PATCH updates - all fields optional"""
    operation: Optional[str] = Field(None, description="Operation type: add, sub, mul, or div")
    operands: Optional[List[float]] = Field(None, min_length=2, description="List of operands (at least 2)")

    @model_validator(mode="after")
    def validate_operation_and_operands(self):
        # Validate operation if provided
        if self.operation is not None:
            valid_operations = ["add", "sub", "mul", "div"]
            if self.operation.lower() not in valid_operations:
                raise ValueError(f"Operation must be one of: {', '.join(valid_operations)}")
        
        # Validate operands length if provided
        if self.operands is not None and len(self.operands) < 2:
            raise ValueError("At least 2 operands are required")
        
        # Note: Division by zero is checked at computation time for partial updates
        
        return self


class CalculationRead(BaseModel):
    id: int
    user_id: int
    operation: str
    operands: List[float]
    result: Optional[float]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)
