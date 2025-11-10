import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import operations


def test_add():
    assert operations.add(2, 3) == 5

def test_subtract():
    assert operations.subtract(5, 3) == 2

def test_multiply():
    assert operations.multiply(2, 3) == 6

def test_divide():
    assert operations.divide(6, 2) == 3

def test_divide_by_zero():
    with pytest.raises(ValueError):
        operations.divide(6, 0)
