from enum import Enum
from typing import Callable


class OperationType(str, Enum):
    Add = "Add"
    Sub = "Sub"
    Multiply = "Multiply"
    Divide = "Divide"


def _add(a: float, b: float) -> float:
    return a + b


def _sub(a: float, b: float) -> float:
    return a - b


def _mul(a: float, b: float) -> float:
    return a * b


def _div(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


_OPERATION_MAP: dict[OperationType, Callable[[float, float], float]] = {
    OperationType.Add: _add,
    OperationType.Sub: _sub,
    OperationType.Multiply: _mul,
    OperationType.Divide: _div,
}


def compute_result(a: float, b: float, op: OperationType) -> float:
    """Compute the result for given operands and operation type.

    Raises ValueError for invalid operations (e.g., division by zero) or
    KeyError for unknown operation types.
    """
    func = _OPERATION_MAP.get(op)
    if func is None:
        raise KeyError(f"Unsupported operation: {op}")
    return func(a, b)


def get_operation_callable(op: OperationType) -> Callable[[float, float], float]:
    return _OPERATION_MAP[op]
