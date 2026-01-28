"""
Script de diagnóstico para PyParseJson
Detecta dónde se pierden los tokens durante el procesamiento
"""

from pyparsejson.core.repair import Repair
from pyparsejson.core.context import Context
from pyparsejson.phases.tokenize import TolerantTokenizer


def diagnose_case(text: str):
    """Diagnóstico completo de un caso"""
    print(f"\n{'=' * 70}")
    print(f"DIAGNÓSTICO: {text[:50]}...")
    print(f"{'=' * 70}")

    # 1. Tokenización inicial
    tokenizer = TolerantTokenizer()
    tokens = tokenizer.tokenize(text)

    print(f"\n1️⃣ TOKENS INICIALES ({len(tokens)}):")
    for i, t in enumerate(tokens[:15]):  # Mostrar primeros 15
        print(f"   [{i}] {t.type.name:15s} = '{t.value}'")

    # 2. Crear contexto y procesar
    context = Context(text)
    context.tokens = tokens

    print(f"\n2️⃣ ANTES DE REGLAS:")
    print(f"   Tokens: {len(context.tokens)}")
    print(f"   Texto reconstruido: {context.get_tokens_as_string()[:100]}")

    # 3. Ejecutar pipeline completo
    repair = Repair(auto_flows=True, debug=True)
    report = repair.parse(text)

    print(f"\n3️⃣ DESPUÉS DE REPARACIÓN:")
    print(f"   Success: {report.success}")
    print(f"   Reglas aplicadas: {report.applied_rules}")
    print(f"   JSON final: {report.json_text}")
    print(f"   Python object: {report.python_object}")

    # 4. Análisis de tokens finales
    if hasattr(context, 'tokens'):
        print(f"\n4️⃣ TOKENS FINALES ({len(context.tokens)}):")
        for i, t in enumerate(context.tokens[:15]):
            print(f"   [{i}] {t.type.name:15s} = '{t.value}'")

    # 5. Detectar problema específico
    if report.success and report.python_object == {}:
        print(f"\n⚠️ PROBLEMA DETECTADO:")
        print(f"   ❌ El caso fue marcado como exitoso pero retornó objeto vacío")
        print(f"   🔍 Posibles causas:")
        print(f"      1. Los tokens se perdieron durante el procesamiento")
        print(f"      2. El finalizador no está procesando los tokens correctamente")
        print(f"      3. json.loads() falló silenciosamente y se aplicó fallback")


if __name__ == "__main__":
    # Casos problemáticos
    test_cases = [
        'user: "admin", active: si',
        'user=admin, active=no',
        'enabled: true, retries: 3',
        'permissions: (read, write, execute)',  # Este SÍ funciona
    ]

    for case in test_cases:
        diagnose_case(case)
        # input("\nPresiona ENTER para continuar...")