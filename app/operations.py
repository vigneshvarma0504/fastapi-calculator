from enum import Enum
from typing import Callable, List


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


# New function for variable-length operands
def compute_result_multi(operands: List[float], operation: str) -> float:
    """Compute the result for given operands and operation string.
    
    Args:
        operands: List of numbers to operate on (must have at least 2 elements)
        operation: Operation name - "add", "sub", "mul", or "div"
    
    Returns:
        The computed result
        
    Raises:
        ValueError: For invalid operations (e.g., division by zero, invalid operands, or unsupported operation)
    """
    if not operands or len(operands) < 2:
        raise ValueError("At least 2 operands are required")
    
    # Normalize operation string to OperationType enum
    operation_map = {
        "add": OperationType.Add,
        "sub": OperationType.Sub,
        "mul": OperationType.Multiply,
        "div": OperationType.Divide,
    }
    
    op_type = operation_map.get(operation.lower())
    if op_type is None:
        raise ValueError(f"Unsupported operation: {operation}")
    
    # For add and multiply, we can reduce over all operands
    if op_type == OperationType.Add:
        return sum(operands)
    elif op_type == OperationType.Multiply:
        result = 1.0
        for num in operands:
            result *= num
        return result
    # For subtract and divide, apply left-to-right
    elif op_type == OperationType.Sub:
        result = operands[0]
        for num in operands[1:]:
            result -= num
        return result
    elif op_type == OperationType.Divide:
        result = operands[0]
        for num in operands[1:]:
            if num == 0:
                raise ValueError("Division by zero is not allowed")
            result /= num
        return result
    
    # This should never be reached due to the check above
    raise ValueError(f"Unsupported operation: {operation}")  # pragma: no cover
