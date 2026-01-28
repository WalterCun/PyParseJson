from pyparsejson import loads
import json

print("🧪 PRUEBA PASO 1: Extracción + Continuación de Reparación\n")

# Caso 1: Texto mixto con JSON anidado → DEBE extraer Y reparar
try:
    result = loads('hola este es un objeto json {hola: mundo} y texto extra')
    print(f"✅ CASO 1 (mixto): {result}")
    assert result == {"hola": "mundo"}, "El resultado debe ser {'hola': 'mundo'}"
except json.JSONDecodeError as e:
    print(f"❌ CASO 1 (mixto): Falló → {str(e)[:80]}...")

# Caso 2: Texto sin estructura → DEBE fallar explícitamente
try:
    result = loads('hola mundo esto no es json')
    print(f"❌ CASO 2 (texto plano): Devolvió {result} (debería fallar)")
except json.JSONDecodeError as e:
    print(f"✅ CASO 2 (texto plano): Falló correctamente")

# Caso 3: Pares sueltos → DEBE envolverse y repararse
try:
    result = loads('user: "admin", active: si')
    print(f"✅ CASO 3 (pares sueltos): {result}")
    assert result == {"user": "admin", "active": True}
except Exception as e:
    print(f"❌ CASO 3 (pares sueltos): {e}")