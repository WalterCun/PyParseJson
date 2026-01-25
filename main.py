import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyparsejson.core.pipeline import Pipeline
from pyparsejson.models.repair_report import Report
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.rules.base import Rule
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType

# --- DEMO DE EXTENSIBILIDAD ---
# Definimos una nueva regla "al vuelo" para demostrar que el sistema es dinámico.
@RuleRegistry.register(tags=["values"], priority=55)
class UpperCaseKeysRule(Rule):
    """
    Regla de ejemplo: Convierte claves específicas a mayúsculas.
    """
    def applies(self, context: Context) -> bool:
        return True

    def apply(self, context: Context):
        # Solo como demo, convertimos 'ciudad' a 'CIUDAD' si existe
        for token in context.tokens:
            if token.type == TokenType.STRING and "ciudad" in token.value:
                token.value = token.value.replace("ciudad", "CIUDAD")
                context.record_rule(self.name)

# --- FIN DEMO EXTENSIBILIDAD ---

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    print(f"\n{Colors.HEADER}════════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.BOLD}ESCENARIO: {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}════════════════════════════════════════════════════════════{Colors.ENDC}")

def print_report(input_text: str, report: Report):
    print(f"\n{Colors.CYAN}► INPUT ORIGINAL:{Colors.ENDC}")
    print(f"{input_text.strip()}\n")

    print(f"{Colors.BLUE}► FLUJO AUTOMÁTICO EJECUTADO{Colors.ENDC}")
    print(f"{Colors.BLUE}► REINTENTOS: {report.iterations}{Colors.ENDC}")

    if report.success:
        print(f"\n{Colors.GREEN}► RESULTADO:{Colors.ENDC}")
        try:
            formatted_json = json.dumps(report.python_object, indent=2)
            print(formatted_json)
        except:
            print(report.json_text)

        print(f"\n{Colors.GREEN}► VALIDACIÓN:{Colors.ENDC}")
        print(f"  ✅ JSON válido")
        
        print(f"\n{Colors.BOLD}► REGLAS APLICADAS ({len(report.applied_rules)}):{Colors.ENDC}")
        for rule in report.applied_rules:
            print(f"  • {rule}")
    else:
        print(f"\n{Colors.FAIL}► FALLO EN LA REPARACIÓN:{Colors.ENDC}")
        print(f"  ❌ No se pudo generar un JSON válido.")
        if report.json_text:
            print(f"\n{Colors.WARNING}► INTENTO FINAL:{Colors.ENDC}")
            print(report.json_text)

    print("\n")

def run_demo():
    # El pipeline ahora descubre automáticamente las reglas registradas
    pipeline = Pipeline()

    # 1️⃣ Caso Frankenstein
    scenario_frankenstein = """
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
    print_header("Reparación Automática – JSON Frankenstein")
    report = pipeline.parse(scenario_frankenstein)
    print_report(scenario_frankenstein, report)

    # 2️⃣ Caso Extensibilidad (Regla Custom)
    scenario_custom = """
    nombre: "Juan",
    ciudad: "Madrid"
    """
    print_header("Extensibilidad – Regla Custom (ciudad -> CIUDAD)")
    report_custom = pipeline.parse(scenario_custom)
    print_report(scenario_custom, report_custom)

if __name__ == "__main__":
    try:
        os.system('')
    except:
        pass
    print(f"{Colors.BOLD}INICIANDO DEMOSTRACIÓN DE PyParseJson (Arquitectura Extensible){Colors.ENDC}")
    run_demo()
