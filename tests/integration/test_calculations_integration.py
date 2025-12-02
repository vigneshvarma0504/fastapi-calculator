import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Calculation
from app.operations import compute_result, OperationType

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
    db = TestingSessionLocal()
    try:
        # create calculation and compute result
        a, b = 20, 4
        op = OperationType.Divide
        result = compute_result(a, b, op)

        calc = Calculation(a=a, b=b, type=op, result=result)
        db.add(calc)
        db.commit()
        db.refresh(calc)

        assert calc.id is not None
        assert calc.result == 5
        assert calc.type == OperationType.Divide
    finally:
        db.close()
