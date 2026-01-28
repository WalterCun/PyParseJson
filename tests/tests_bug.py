"""
Test específico para identificar el bug exacto
"""
import json
from pyparsejson.core.repair import Repair
from pyparsejson.core.context import Context
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.phases.json_finalize import JSONFinalize


def test_simple_case():
    """Test del caso más simple que está fallando"""

    text = 'user: "admin", active: si'
    print(f"\n{'=' * 70}")
    print(f"TEST: {text}")
    print(f"{'=' * 70}")

    # PASO 1: Tokenización
    tokenizer = TolerantTokenizer()
    tokens = tokenizer.tokenize(text)

    print(f"\n1️⃣ TOKENIZACIÓN:")
    print(f"   Cantidad: {len(tokens)}")
    for i, t in enumerate(tokens):
        print(f"   [{i}] {t.type.name:15s} = '{t.value}'")

    # PASO 2: Crear contexto y aplicar SOLO WrapRootObjectRule manualmente
    context = Context(text)
    context.tokens = tokens.copy()

    from pyparsejson.rules.structure.wrappers import WrapRootObjectRule
    wrap_rule = WrapRootObjectRule()

    if wrap_rule.applies(context):
        print(f"\n2️⃣ APLICANDO WrapRootObjectRule:")
        print(f"   Tokens antes: {len(context.tokens)}")
        wrap_rule.apply(context)
        print(f"   Tokens después: {len(context.tokens)}")

        for i, t in enumerate(context.tokens):
            print(f"   [{i}] {t.type.name:15s} = '{t.value}'")

    # PASO 3: Aplicar AddMissingCommasRule
    from pyparsejson.rules.structure.separators import AddMissingCommasRule
    comma_rule = AddMissingCommasRule()

    if comma_rule.applies(context):
        print(f"\n3️⃣ APLICANDO AddMissingCommasRule:")
        print(f"   Tokens antes: {len(context.tokens)}")
        comma_rule.apply(context)
        print(f"   Tokens después: {len(context.tokens)}")

        for i, t in enumerate(context.tokens):
            print(f"   [{i}] {t.type.name:15s} = '{t.value}'")

    # PASO 4: Finalizar
    finalizer = JSONFinalize()
    json_text = finalizer.process(context)

    print(f"\n4️⃣ FINALIZACIÓN:")
    print(f"   JSON generado: {json_text}")
    print(f"   Longitud: {len(json_text)}")

    # PASO 5: Parse
    try:
        obj = json.loads(json_text)
        print(f"\n5️⃣ PARSING:")
        print(f"   ✅ SUCCESS")
        print(f"   Objeto: {obj}")
    except json.JSONDecodeError as e:
        print(f"\n5️⃣ PARSING:")
        print(f"   ❌ ERROR: {e}")

    # PASO 6: Comparar con pipeline completo
    print(f"\n6️⃣ PIPELINE COMPLETO:")
    repair = Repair(auto_flows=True)
    report = repair.parse(text)
    print(f"   Success: {report.success}")
    print(f"   JSON: {report.json_text}")
    print(f"   Object: {report.python_object}")

    # DIAGNÓSTICO FINAL
    print(f"\n{'=' * 70}")
    if report.python_object == {}:
        print("⚠️ CONFIRMADO: El pipeline completo retorna objeto vacío")
        print("🔍 Causas posibles:")
        print("   1. Los tokens se vacían en algún punto del flujo")
        print("   2. El finalizador no está procesando los tokens")
        print("   3. Hay un error en json.loads() que se captura silenciosamente")
    else:
        print("✅ El pipeline funciona correctamente")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    test_simple_case()