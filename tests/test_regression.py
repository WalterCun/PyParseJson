# tests/test_regression.py
import pytest
from pyparsejson import loads

CASES = [
    ('user: "admin", active: si', {'user': 'admin', 'active': True}),
    ('user=admin, active=no', {'user': 'admin', 'active': False}),
    # ... todos los 31 casos
]

@pytest.mark.parametrize("input_text,expected", CASES)
def test_case(input_text, expected):
    result = loads(input_text)
    assert result == expected