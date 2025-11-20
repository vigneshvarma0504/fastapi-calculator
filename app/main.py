from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, Base, get_db
from .security import hash_password
from .logger_config import setup_logger

logger = setup_logger("fastapi_calculator")  # pragma: no cover

# Create tables
Base.metadata.create_all(bind=engine)  # pragma: no cover

app = FastAPI(title="FastAPI Calculator with Secure User Model")


@app.get("/add")
def add(a: float, b: float):  # pragma: no cover
    result = a + b
    logger.info(f"add called with a={a}, b={b}, result={result}")
    return {"operation": "add", "a": a, "b": b, "result": result}


@app.get("/subtract")
def subtract(a: float, b: float):  # pragma: no cover
    result = a - b
    logger.info(f"subtract called with a={a}, b={b}, result={result}")
    return {"operation": "subtract", "a": a, "b": b, "result": result}


@app.get("/multiply")
def multiply(a: float, b: float):  # pragma: no cover
    result = a * b
    logger.info(f"multiply called with a={a}, b={b}, result={result}")
    return {"operation": "multiply", "a": a, "b": b, "result": result}


@app.get("/divide")
def divide(a: float, b: float):  # pragma: no cover
    if b == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Division by zero is not allowed",
        )
    result = a / b
    logger.info(f"divide called with a={a}, b={b}, result={result}")
    return {"operation": "divide", "a": a, "b": b, "result": result}


@app.post(
    "/users/",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check uniqueness
    existing = (
        db.query(models.User)
        .filter(
            (models.User.username == user_in.username)
            | (models.User.email == user_in.email)
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Created user id={db_user.id}, username={db_user.username}")
    return db_user


@app.get("/users/", response_model=List[schemas.UserRead])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users
