from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, Base, get_db
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    is_refresh_token,
)
from fastapi.security import OAuth2PasswordBearer
from fastapi import Header
from .logger_config import setup_logger

logger = setup_logger("fastapi_calculator")  # pragma: no cover

# Create tables
Base.metadata.create_all(bind=engine)  # pragma: no cover


app = FastAPI(title="FastAPI Calculator with Secure User Model")

# Enable CORS for frontend on port 8081
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://127.0.0.1:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    from fastapi.openapi.utils import get_openapi

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=app.title, version="1.0.0", routes=app.routes)
    # add bearer auth scheme
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # annotate protected paths (simple heuristic)
    for path, methods in openapi_schema.get("paths", {}).items():
        if path.startswith("/calculations") or path.startswith("/users/me") or path.startswith("/admin"):
            for method, op in methods.items():
                op.setdefault("security", []).append({"bearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role: str):
    def role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return current_user

    return role_dependency


@app.post("/users/me/revoke")
def revoke_my_token_by_string(body: schemas.RefreshRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Alias for logout: revoke a refresh token string for the current user."""
    token = body.refresh_token
    from app.models import RefreshToken as RT

    rt = db.query(RT).filter(RT.token == token, RT.user_id == current_user.id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="refresh token not found")
    rt.revoked = True
    db.add(rt)
    db.commit()
    return {"msg": "revoked"}


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


# ------------------- User Profile Management -------------------


@app.get("/users/me", response_model=schemas.UserRead)
def get_current_user_info(
    current_user: models.User = Depends(get_current_user),
):
    """
    Get current user's profile information.
    """
    logger.info(f"User id={current_user.id} retrieved their profile")
    return current_user


@app.patch("/users/me", response_model=schemas.UserRead)
def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current user's profile (username and/or email).
    """
    # Check if username is taken by another user
    if profile_update.username:
        existing = (
            db.query(models.User)
            .filter(
                models.User.username == profile_update.username,
                models.User.id != current_user.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        current_user.username = profile_update.username

    # Check if email is taken by another user
    if profile_update.email:
        existing = (
            db.query(models.User)
            .filter(
                models.User.email == profile_update.email,
                models.User.id != current_user.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken",
            )
        current_user.email = profile_update.email

    db.commit()
    db.refresh(current_user)
    logger.info(f"User id={current_user.id} updated their profile")
    return current_user


@app.post("/users/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_change: schemas.PasswordChangeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change current user's password.
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash and update new password
    current_user.password_hash = hash_password(password_change.new_password)
    db.commit()
    logger.info(f"User id={current_user.id} changed their password")
    return {"message": "Password changed successfully"}


# ------------------- User Registration -------------------


@app.post(
    "/users/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # reuse logic from create_user but expose /users/register
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
    logger.info(f"Registered user id={db_user.id}, username={db_user.username}")
    return db_user



@app.post("/users/login", response_model=schemas.Token)
def login_user(login: schemas.UserLogin, db: Session = Depends(get_db)):
    # allow login via username or email
    if not login.username and not login.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username or email required",
        )

    query = db.query(models.User)
    if login.username:
        query = query.filter(models.User.username == login.username)
    else:
        query = query.filter(models.User.email == login.email)

    user = query.first()
    if not user or not verify_password(login.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # create JWT tokens
    access_token = create_access_token(subject=user.username)
    refresh_token = create_refresh_token(subject=user.username)

    # persist refresh token in RefreshToken table
    from app.models import RefreshToken

    rt = RefreshToken(user_id=user.id, token=refresh_token)
    db.add(rt)
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}



@app.post("/users/refresh", response_model=schemas.Token)
def refresh_token(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    token = body.refresh_token
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token required")

    # ensure token is a refresh token
    if not is_refresh_token(token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # verify token exists in DB and not revoked
    from app.models import RefreshToken as RT

    rt = db.query(RT).filter(RT.token == token, RT.user_id == user.id, RT.revoked == False).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked refresh token")

    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "refresh_token": token, "token_type": "bearer"}


@app.post("/users/logout")
def logout_user(body: schemas.RefreshRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    token = body.refresh_token
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token required")

    from app.models import RefreshToken as RT

    rt = db.query(RT).filter(RT.token == token, RT.user_id == current_user.id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="refresh token not found")

    rt.revoked = True
    db.add(rt)
    db.commit()
    return {"msg": "logged out"}



@app.post("/users/{username}/role", response_model=schemas.UserRead)
def set_user_role(username: str, payload: schemas.RoleUpdate, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/me/tokens", response_model=list[schemas.RefreshTokenRead])
def list_my_tokens(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import RefreshToken as RT

    tokens = db.query(RT).filter(RT.user_id == current_user.id).all()
    return tokens


@app.delete("/users/me/tokens/{token_id}")
def revoke_my_token(token_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import RefreshToken as RT

    rt = db.query(RT).filter(RT.id == token_id, RT.user_id == current_user.id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="refresh token not found")
    rt.revoked = True
    db.add(rt)
    db.commit()
    return {"msg": "revoked"}


@app.post("/users/{username}/revoke_all")
def revoke_all_for_user(username: str, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    from app.models import RefreshToken as RT

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.query(RT).filter(RT.user_id == user.id).update({RT.revoked: True})
    db.commit()
    return {"msg": "revoked all"}


@app.get("/admin/tokens", response_model=list[schemas.RefreshTokenRead])
def admin_list_all_tokens(_=Depends(require_role("admin")), db: Session = Depends(get_db)):
    from app.models import RefreshToken as RT

    tokens = db.query(RT).all()
    return tokens


@app.get("/admin/users/{username}/tokens", response_model=list[schemas.RefreshTokenRead])
def admin_list_tokens_for_user(username: str, _=Depends(require_role("admin")), db: Session = Depends(get_db)):
    from app.models import RefreshToken as RT

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tokens = db.query(RT).filter(RT.user_id == user.id).all()
    return tokens


@app.post("/admin/tokens/revoke")
def admin_revoke_by_token(body: schemas.RefreshRequest, _=Depends(require_role("admin")), db: Session = Depends(get_db)):
    token = body.refresh_token
    from app.models import RefreshToken as RT

    rt = db.query(RT).filter(RT.token == token).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    rt.revoked = True
    db.add(rt)
    db.commit()
    return {"msg": "revoked"}


@app.get("/admin/users", response_model=list[schemas.UserWithTokenCount])
def admin_list_users(skip: int = 0, limit: int = 100, _=Depends(require_role("admin")), db: Session = Depends(get_db)):
    """List users with count of refresh tokens. Admin-only. Supports pagination via skip/limit."""
    # left join users with refresh_tokens and count
    from sqlalchemy import func
    from app.models import RefreshToken as RT

    q = (
        db.query(models.User.id, models.User.username, models.User.email, models.User.role, func.count(RT.id).label("token_count"))
        .outerjoin(RT, RT.user_id == models.User.id)
        .group_by(models.User.id)
        .offset(skip)
        .limit(limit)
    )
    results = q.all()

    # convert to list of dicts/objects compatible with schema
    users = []
    for r in results:
        users.append({"id": r.id, "username": r.username, "email": r.email, "role": r.role, "token_count": int(r.token_count)})
    return users


@app.get("/users/", response_model=List[schemas.UserRead])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_role("admin"))):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@app.get("/calculations", response_model=List[schemas.CalculationRead])
def list_calculations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Browse: Retrieve all calculations belonging to the logged-in user."""
    calcs = db.query(models.Calculation).filter(models.Calculation.user_id == current_user.id).offset(skip).limit(limit).all()
    return calcs


@app.post(
    "/calculations",
    response_model=schemas.CalculationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_calculation(calc_in: schemas.CalculationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Add: Create a new calculation for the current user."""
    # compute result using business logic
    from app.operations import compute_result

    result = compute_result(calc_in.a, calc_in.b, calc_in.type)

    db_calc = models.Calculation(
        user_id=current_user.id,
        a=calc_in.a, 
        b=calc_in.b, 
        type=calc_in.type, 
        result=result
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc


@app.get("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def read_calculation(calc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Read: Retrieve details of a specific calculation by its ID."""
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id
    ).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")
    return calc


@app.put("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def update_calculation(calc_id: int, calc_in: schemas.CalculationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Edit (PUT): Replace an existing calculation with new data."""
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id
    ).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")

    from app.operations import compute_result

    calc.a = calc_in.a
    calc.b = calc_in.b
    calc.type = calc_in.type
    calc.result = compute_result(calc.a, calc.b, calc.type)
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@app.patch("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def partial_update_calculation(calc_id: int, calc_in: schemas.CalculationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Edit (PATCH): Partially update an existing calculation."""
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id
    ).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")

    # Update only provided fields
    if calc_in.a is not None:
        calc.a = calc_in.a
    if calc_in.b is not None:
        calc.b = calc_in.b
    if calc_in.type is not None:
        calc.type = calc_in.type
    
    # Recompute result
    from app.operations import compute_result
    calc.result = compute_result(calc.a, calc.b, calc.type)
    
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(calc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Delete: Remove a calculation by its ID."""
    calc = db.query(models.Calculation).filter(
        models.Calculation.id == calc_id,
        models.Calculation.user_id == current_user.id
    ).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")
    db.delete(calc)
    db.commit()
    return None
