from pyparsejson import loads
import json

# Caso 1: Texto mixto con JSON anidado → DEBE extraer el objeto
try:
    result = loads('hola este es un objeto json {hola: mundo} y texto extra')
    print(f"✅ CASO 1 (mixto): {result}")  # Esperado: {"hola": "mundo"}
except json.JSONDecodeError as e:
    print(f"⚠️ CASO 1 (mixto): {e}")

# Caso 2: Texto sin estructura → DEBE fallar explícitamente
try:
    result = loads('hola mundo esto no es json')
    print(f"❌ CASO 2 (texto plano): Devolvió {result} (debería fallar)")
except json.JSONDecodeError as e:
    print(f"✅ CASO 2 (texto plano): Falló correctamente → {str(e)[:60]}...")

# Caso 3: JSON válido → DEBE parsear correctamente
result = loads('user: "admin", active: si')
print(f"✅ CASO 3 (pares sueltos): {result}")  # Aún fallará hasta implementar WrapRootObjectRule