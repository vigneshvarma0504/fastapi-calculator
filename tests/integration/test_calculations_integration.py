import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Calculation, User
from app.operations import compute_result_multi
from app.security import hash_password

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test_integration.db",
)

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_insert_and_read_calculation():
    """Test creating and reading a calculation with new schema."""
    db = TestingSessionLocal()
    try:
        # Create a user first (required for foreign key)
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # create calculation with new schema
        operands = [20, 4]
        operation = "div"
        result = compute_result_multi(operands, operation)

        calc = Calculation(
            user_id=user.id,
            operation=operation,
            operands=operands,
            result=result
        )
        db.add(calc)
        db.commit()
        db.refresh(calc)

        assert calc.id is not None
        assert calc.result == 5
        assert calc.operation == "div"
        assert calc.operands == [20, 4]
        assert calc.user_id == user.id
    finally:
        db.close()
