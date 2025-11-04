import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_add_endpoint():
    response = client.get("/add?a=2&b=3")
    assert response.status_code == 200
    assert response.json() == {"result": 5}

def test_divide_by_zero_endpoint():
    response = client.get("/divide?a=4&b=0")
    assert response.status_code == 400
