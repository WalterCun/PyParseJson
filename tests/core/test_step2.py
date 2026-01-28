from pyparsejson import loads
import json

print("🧪 PRUEBA PASO 2: QuoteBareWordsRule Corregido\n")

# Caso 1: Texto mixto con JSON anidado → DEBE extraer Y reparar claves/valores
try:
    result = loads('hola este es un objeto json {hola: mundo} y texto extra')
    print(f"✅ CASO 1 (mixto): {result}")
    assert result == {"hola": "mundo"}, f"Esperado {{'hola': 'mundo'}}, obtenido {result}"
except json.JSONDecodeError as e:
    print(f"❌ CASO 1 (mixto): Falló → {str(e)[:80]}...")

# Caso 2: Claves y valores sin comillas → DEBE quotar ambos
try:
    result = loads('user: admin, active: si')
    print(f"✅ CASO 2 (pares sueltos): {result}")
    assert result == {"user": "admin", "active": True}
except Exception as e:
    print(f"❌ CASO 2 (pares sueltos): {e}")

# Caso 3: Valores numéricos → NO deben ser quotados
try:
    result = loads('count: 42, enabled: true')
    print(f"✅ CASO 3 (números/booleanos): {result}")
    assert result == {"count": 42, "enabled": True}, f"Tipo incorrecto: {type(result['count'])}"
except Exception as e:
    print(f"❌ CASO 3 (números/booleanos): {e}")