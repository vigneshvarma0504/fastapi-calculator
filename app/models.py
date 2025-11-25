from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, Float, Enum as SQLEnum
from .database import Base

from app.operations import OperationType


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Calculation(Base):
    """Persistent calculation record.

    Stores the operands, operation type and the computed result. The result is
    computed by business logic (see `app.operations`) and stored at creation.
    """

    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    # store operation as an enum (Add, Sub, Multiply, Divide)
    type = Column(SQLEnum(OperationType, name="operation_type"), nullable=False)
    # store result to make querying easier; can be computed on demand alternatively
    result = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
