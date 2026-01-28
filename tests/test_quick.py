from pyparsejson import loads

# Test 1: Caso simple
result = loads('user: "admin", active: si')
print(f"Test 1: {result}")
assert result == {'user': 'admin', 'active': True}, f"❌ Esperado {{'user': 'admin', 'active': True}}, obtenido {result}"
print("✅ Test 1 PASSED")

# Test 2: Con igual
result = loads('user=admin, active=no')
print(f"Test 2: {result}")
assert result == {'user': 'admin', 'active': False}, f"❌ Esperado {{'user': 'admin', 'active': False}}, obtenido {result}"
print("✅ Test 2 PASSED")

# Test 3: Sin comas
result = loads('user: admin active: si role: superuser')
print(f"Test 3: {result}")
assert result == {'user': 'admin', 'active': True, 'role': 'superuser'}
print("✅ Test 3 PASSED")

print("\n🎉 TODOS LOS TESTS PASARON")