# test_critical_fixes.py
import pytest
from pyparsejson import loads

def test_add_missing_commas_simple():
    """Caso 1: Pares sueltos simples"""
    result = loads('user: "admin", active: si')
    assert result == {'user': 'admin', 'active': True}

def test_add_missing_commas_multiple():
    """Caso 3: Sin comas entre claves"""
    result = loads('user: admin active: si role: superuser')
    assert result == {'user': 'admin', 'active': True, 'role': 'superuser'}

def test_strip_prefix_sql():
    """Caso 24: Log de aplicación tipo SQL"""
    result = loads('INSERT INTO users (id, name) VALUES (1, "Carlos")')
    assert result == {}  # No hay estructura JSON válida

def test_strip_prefix_natural_language():
    """Caso 26: Texto casi libre"""
    result = loads('hola mundo esto no es json pero tiene clave:valor')
    assert result == {'clave': 'valor'}

def test_normalize_booleans():
    """Verificar que si/no se convierten correctamente"""
    result = loads('active: si, enabled: no')
    assert result == {'active': True, 'enabled': False}

def test_no_duplicate_wrapping():
    """Verificar que no se envuelve múltiples veces"""
    result = loads('{"a": 1}')
    assert result == {'a': 1}
    # No debe ser: {"{"a": 1}"}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])