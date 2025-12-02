import pytest
from pydantic import ValidationError

from app.operations import compute_result, OperationType
from app.schemas import CalculationCreate


def test_compute_basic_operations():
    assert compute_result(1, 2, OperationType.Add) == 3
    assert compute_result(5, 3, OperationType.Sub) == 2
    assert compute_result(4, 3, OperationType.Multiply) == 12
    assert compute_result(10, 2, OperationType.Divide) == 5


def test_compute_division_by_zero_raises():
    with pytest.raises(ValueError):
        compute_result(1, 0, OperationType.Divide)


def test_calculationcreate_valid_and_invalid():
    # valid
    c = CalculationCreate(a=10, b=5, type=OperationType.Divide)
    assert c.a == 10

    # invalid division by zero should raise ValidationError
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=0, type=OperationType.Divide)
