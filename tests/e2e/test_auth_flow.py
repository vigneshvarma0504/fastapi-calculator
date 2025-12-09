import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid


# Use a separate test database for E2E tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_e2e.db")

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def unique_user(prefix):
    """Generate unique user credentials."""
    u = str(uuid.uuid4())[:8]
    return {
        "username": f"{prefix}_{u}",
        "email": f"{prefix}_{u}@example.com",
        "password": "password123"
    }


def register_and_login(prefix="user"):
    """Helper to register and login a user, returns headers with token."""
    user = unique_user(prefix)
    
    # Register
    r = client.post("/users/register", json=user)
    assert r.status_code == 201, f"Registration failed: {r.text}"
    
    # Login
    r = client.post("/users/login", json={"username": user["username"], "password": user["password"]})
    assert r.status_code == 200, f"Login failed: {r.text}"
    
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Positive Scenarios

def test_e2e_create_read_calculation():
    """E2E: Create a calculation and read it back."""
    headers = register_and_login("e2e_create")
    
    # Create
    payload = {"operation": "add", "operands": [10, 20, 5]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["result"] == 35
    calc_id = data["id"]
    
    # Read
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == calc_id
    assert data["operation"] == "add"
    assert data["operands"] == [10, 20, 5]
    assert data["result"] == 35


def test_e2e_list_calculations():
    """E2E: Create multiple calculations and list them."""
    headers = register_and_login("e2e_list")
    
    # Create 3 calculations
    for i in range(3):
        payload = {"operation": "mul", "operands": [i + 1, 2]}
        r = client.post("/calculations", json=payload, headers=headers)
        assert r.status_code == 201
    
    # List
    r = client.get("/calculations", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3


def test_e2e_update_calculation_put():
    """E2E: Create and update a calculation using PUT."""
    headers = register_and_login("e2e_update")
    
    # Create
    payload = {"operation": "sub", "operands": [100, 25]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    calc_id = r.json()["id"]
    assert r.json()["result"] == 75
    
    # Update
    new_payload = {"operation": "div", "operands": [100, 5]}
    r = client.put(f"/calculations/{calc_id}", json=new_payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["operation"] == "div"
    assert data["result"] == 20


def test_e2e_update_calculation_patch():
    """E2E: Partially update a calculation using PATCH."""
    headers = register_and_login("e2e_patch")
    
    # Create
    payload = {"operation": "add", "operands": [1, 2, 3]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    calc_id = r.json()["id"]
    
    # Patch - change only operands
    patch_payload = {"operands": [10, 20, 30]}
    r = client.patch(f"/calculations/{calc_id}", json=patch_payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["operation"] == "add"
    assert data["operands"] == [10, 20, 30]
    assert data["result"] == 60


def test_e2e_delete_calculation():
    """E2E: Create and delete a calculation."""
    headers = register_and_login("e2e_delete")
    
    # Create
    payload = {"operation": "mul", "operands": [3, 4]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    calc_id = r.json()["id"]
    
    # Delete
    r = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 204
    
    # Verify deleted
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 404


def test_e2e_multiple_operands():
    """E2E: Test calculations with more than 2 operands."""
    headers = register_and_login("e2e_multi")
    
    # Add with 5 operands
    payload = {"operation": "add", "operands": [1, 2, 3, 4, 5]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    assert r.json()["result"] == 15
    
    # Multiply with 4 operands
    payload = {"operation": "mul", "operands": [2, 2, 2, 2]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201
    assert r.json()["result"] == 16


# Negative Scenarios

def test_e2e_unauthenticated_access_returns_401():
    """E2E: Accessing endpoints without authentication returns 401."""
    # List without auth
    r = client.get("/calculations")
    assert r.status_code == 401
    
    # Create without auth
    r = client.post("/calculations", json={"operation": "add", "operands": [1, 2]})
    assert r.status_code == 401
    
    # Read without auth
    r = client.get("/calculations/1")
    assert r.status_code == 401
    
    # Update without auth
    r = client.put("/calculations/1", json={"operation": "add", "operands": [1, 2]})
    assert r.status_code == 401
    
    # Delete without auth
    r = client.delete("/calculations/1")
    assert r.status_code == 401


def test_e2e_access_other_user_calculation_returns_403():
    """E2E: Users cannot access other users' calculations."""
    # User 1 creates a calculation
    headers1 = register_and_login("e2e_user1")
    payload = {"operation": "add", "operands": [5, 10]}
    r = client.post("/calculations", json=payload, headers=headers1)
    assert r.status_code == 201
    calc_id = r.json()["id"]
    
    # User 2 tries to access user 1's calculation
    headers2 = register_and_login("e2e_user2")
    
    # Read - should get 403
    r = client.get(f"/calculations/{calc_id}", headers=headers2)
    assert r.status_code == 403
    
    # Update - should get 403
    r = client.put(f"/calculations/{calc_id}", json={"operation": "mul", "operands": [2, 3]}, headers=headers2)
    assert r.status_code == 403
    
    # Delete - should get 403
    r = client.delete(f"/calculations/{calc_id}", headers=headers2)
    assert r.status_code == 403


def test_e2e_division_by_zero_returns_422():
    """E2E: Division by zero returns 422 validation error."""
    headers = register_and_login("e2e_divzero")
    
    payload = {"operation": "div", "operands": [10, 0]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 422


def test_e2e_invalid_operation_returns_422():
    """E2E: Invalid operation returns 422 validation error."""
    headers = register_and_login("e2e_invalid_op")
    
    payload = {"operation": "invalid", "operands": [10, 5]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 422


def test_e2e_insufficient_operands_returns_422():
    """E2E: Less than 2 operands returns 422 validation error."""
    headers = register_and_login("e2e_insufficient")
    
    payload = {"operation": "add", "operands": [10]}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 422


def test_e2e_not_found_returns_404():
    """E2E: Accessing non-existent calculation returns 404."""
    headers = register_and_login("e2e_notfound")
    
    # Read non-existent
    r = client.get("/calculations/99999", headers=headers)
    assert r.status_code == 404
    
    # Update non-existent
    r = client.put("/calculations/99999", json={"operation": "add", "operands": [1, 2]}, headers=headers)
    assert r.status_code == 404
    
    # Delete non-existent
    r = client.delete("/calculations/99999", headers=headers)
    assert r.status_code == 404


def test_e2e_complete_workflow():
    """E2E: Complete workflow - create, list, update, verify, delete."""
    headers = register_and_login("e2e_workflow")
    
    # Create first calculation
    r = client.post("/calculations", json={"operation": "add", "operands": [10, 20]}, headers=headers)
    assert r.status_code == 201
    calc1_id = r.json()["id"]
    
    # Create second calculation
    r = client.post("/calculations", json={"operation": "mul", "operands": [3, 4, 5]}, headers=headers)
    assert r.status_code == 201
    calc2_id = r.json()["id"]
    
    # List - should see both
    r = client.get("/calculations", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2
    
    # Update first calculation
    r = client.put(f"/calculations/{calc1_id}", json={"operation": "sub", "operands": [100, 25]}, headers=headers)
    assert r.status_code == 200
    assert r.json()["result"] == 75
    
    # Verify update
    r = client.get(f"/calculations/{calc1_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["operation"] == "sub"
    assert r.json()["result"] == 75
    
    # Delete second calculation
    r = client.delete(f"/calculations/{calc2_id}", headers=headers)
    assert r.status_code == 204
    
    # List - should see only first
    r = client.get("/calculations", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == calc1_id
