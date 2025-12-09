import pytest
from pydantic import ValidationError

from app.operations import compute_result, compute_result_multi, OperationType
from app.schemas import CalculationCreate


def test_compute_basic_operations():
    assert compute_result(1, 2, OperationType.Add) == 3
    assert compute_result(5, 3, OperationType.Sub) == 2
    assert compute_result(4, 3, OperationType.Multiply) == 12
    assert compute_result(10, 2, OperationType.Divide) == 5


def test_compute_division_by_zero_raises():
    with pytest.raises(ValueError):
        compute_result(1, 0, OperationType.Divide)


def test_compute_result_multi_operations():
    """Test new multi-operand computation."""
    assert compute_result_multi([1, 2, 3], "add") == 6
    assert compute_result_multi([10, 2, 3], "sub") == 5
    assert compute_result_multi([2, 3, 4], "mul") == 24
    assert compute_result_multi([100, 2, 5], "div") == 10


def test_compute_result_multi_division_by_zero():
    """Test division by zero raises error."""
    with pytest.raises(ValueError):
        compute_result_multi([10, 0], "div")


def test_compute_result_multi_invalid_operation():
    """Test invalid operation raises error."""
    with pytest.raises(ValueError):
        compute_result_multi([1, 2], "invalid")


def test_compute_result_multi_insufficient_operands():
    """Test insufficient operands raises error."""
    with pytest.raises(ValueError):
        compute_result_multi([1], "add")


def test_calculationcreate_valid():
    """Test valid calculation creation with new schema."""
    c = CalculationCreate(operation="add", operands=[10, 5, 3])
    assert c.operation == "add"
    assert c.operands == [10, 5, 3]


def test_calculationcreate_invalid_division_by_zero():
    """Test division by zero validation in schema."""
    with pytest.raises(ValidationError):
        CalculationCreate(operation="div", operands=[1, 0])


def test_calculationcreate_invalid_operation():
    """Test invalid operation raises validation error."""
    with pytest.raises(ValidationError):
        CalculationCreate(operation="invalid", operands=[1, 2])


def test_calculationcreate_insufficient_operands():
    """Test insufficient operands raises validation error."""
    with pytest.raises(ValidationError):
        CalculationCreate(operation="add", operands=[1])
