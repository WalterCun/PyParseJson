import json
import sys
import os

# Aseguramos que el path del proyecto esté en sys.path para poder importar ppj
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppj.engine.context import Context
from ppj.engine.stages.repair import RepairStage

def run_demo(title, input_text):
    """
    Ejecuta una demostración de reparación sobre un texto dado.
    """
    print(f"════════════════════════════════════════════════════════════")
    print(f"ESCENARIO: {title}")
    print(f"════════════════════════════════════════════════════════════")
    print(f"► INPUT ORIGINAL:\n{input_text}\n")

    # 1. Crear Contexto
    ctx = Context(input_text)

    # 2. Inicializar Stage de Reparación
    repair_stage = RepairStage()

    # 3. Procesar
    print("► PROCESANDO...")
    repair_stage.process(ctx)

    # 4. Mostrar Resultados
    print(f"► OUTPUT REPARADO:\n{ctx.current_text}\n")
    
    print(f"► REGLAS APLICADAS ({len(ctx.applied_rules)}):")
    for rule in ctx.applied_rules:
        print(f"  • {rule}")
    
    # 5. Validación final con json.loads
    print("\n► VALIDACIÓN JSON:")
    try:
        parsed_obj = json.loads(ctx.current_text)
        print("  ✅ ÉXITO: El resultado es un JSON válido.")
        print(f"  🔍 Objeto Python: {parsed_obj}")
    except json.JSONDecodeError as e:
        print(f"  ❌ ERROR: Aún no es JSON válido.")
        print(f"  Details: {e}")
    
    print("\n")


def main():
    print("INICIANDO DEMOSTRACIÓN MANUAL DE PyParseJson (Fase 1: Reparación)\n")

    # CASO 1: Sintaxis Básica Rota
    # - Claves sin comillas
    # - Uso de = en lugar de :
    # - Comas faltantes
    text_basic = """
    nombre=Juan
    edad=30
    ciudad: Madrid
    """
    run_demo("Sintaxis Básica y Separadores", text_basic)


    # CASO 2: Literales y Tipos de Datos
    # - Booleanos en español (si/no)
    # - Tuplas en lugar de listas
    # - Fechas sin comillas
    text_literals = """
    {
        activo: si,
        admin: no,
        permisos: (leer, escribir, ejecutar),
        fecha_registro: 2023-10-27
    }
    """
    run_demo("Literales, Tuplas y Fechas", text_literals)


    # CASO 3: Estructura Incompleta
    # - Falta cerrar llaves
    # - Comas sobrantes al final
    text_structure = '{"data": [1, 2, 3, ], "status": "ok"'
    run_demo("Cierre de Estructuras y Comas Sobrantes", text_structure)


    # CASO 4: El 'Frankenstein' (Todo junto)
    # - Input muy sucio simulando logs o respuestas de LLMs mal formadas
    text_messy = """
    user_id=998877
    preferences: {
        theme: dark,
        notifications: (email, sms)
    }
    verified: si
    history: [
        login, logout,
    ]
    """
    run_demo("Caso Complejo 'Frankenstein'", text_messy)

if __name__ == "__main__":
    main()
