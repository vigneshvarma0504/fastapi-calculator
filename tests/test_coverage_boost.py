"""
Additional tests to achieve 100% code coverage.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.operations import get_operation_callable, OperationType
from app import schemas
from pydantic import ValidationError


client = TestClient(app)


def test_openapi_schema_generation():
    """Test that custom OpenAPI schema is generated correctly."""
    # Access the OpenAPI schema which triggers custom_openapi()
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    
    # Verify bearerAuth security scheme is present
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "bearerAuth" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["bearerAuth"]["type"] == "http"
    assert schema["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    
    # Verify protected paths have security
    paths = schema.get("paths", {})
    for path in paths:
        if "/calculations" in path or "/users/me" in path or "/admin" in path:
            for method in paths[path]:
                if method != "parameters":
                    operation = paths[path][method]
                    # Should have security defined
                    if "security" in operation:
                        assert {"bearerAuth": []} in operation["security"]


def test_openapi_schema_caching():
    """Test that OpenAPI schema is cached after first generation."""
    # First call generates schema
    response1 = client.get("/openapi.json")
    assert response1.status_code == 200
    
    # Second call should return cached schema
    response2 = client.get("/openapi.json")
    assert response2.status_code == 200
    
    # Both should be identical
    assert response1.json() == response2.json()


def test_get_operation_callable():
    """Test get_operation_callable function."""
    # Test getting callable for each operation type
    add_func = get_operation_callable(OperationType.Add)
    assert add_func(5, 3) == 8
    
    sub_func = get_operation_callable(OperationType.Sub)
    assert sub_func(5, 3) == 2
    
    mul_func = get_operation_callable(OperationType.Multiply)
    assert mul_func(5, 3) == 15
    
    div_func = get_operation_callable(OperationType.Divide)
    assert div_func(6, 3) == 2


def test_get_operation_callable_keyerror():
    """Test that get_operation_callable raises KeyError for invalid operation."""
    # This should raise KeyError since we're accessing the dict directly
    with pytest.raises(KeyError):
        get_operation_callable("InvalidOperation")


def test_calculation_update_schema_division_by_zero():
    """Test CalculationUpdate schema validation for division by zero."""
    # Valid update
    valid_update = schemas.CalculationUpdate(a=10, b=5, type=OperationType.Divide)
    assert valid_update.a == 10
    assert valid_update.b == 5
    
    # Invalid: division by zero
    with pytest.raises(ValueError, match="Division by zero is not allowed"):
        schemas.CalculationUpdate(a=10, b=0, type=OperationType.Divide)
    
    # Valid: b is None (partial update)
    partial_update = schemas.CalculationUpdate(a=10, type=OperationType.Divide)
    assert partial_update.a == 10
    assert partial_update.b is None
    
    # Valid: b is not zero
    valid_divide = schemas.CalculationUpdate(b=5, type=OperationType.Divide)
    assert valid_divide.b == 5


def test_calculation_update_schema_optional_fields():
    """Test CalculationUpdate schema with optional fields."""
    # Only a
    update1 = schemas.CalculationUpdate(a=10)
    assert update1.a == 10
    assert update1.b is None
    assert update1.type is None
    
    # Only b
    update2 = schemas.CalculationUpdate(b=5)
    assert update2.a is None
    assert update2.b == 5
    assert update2.type is None
    
    # Only type
    update3 = schemas.CalculationUpdate(type=OperationType.Add)
    assert update3.a is None
    assert update3.b is None
    assert update3.type == OperationType.Add
    
    # All fields
    update4 = schemas.CalculationUpdate(a=10, b=5, type=OperationType.Multiply)
    assert update4.a == 10
    assert update4.b == 5
    assert update4.type == OperationType.Multiply
