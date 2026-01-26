import sys
import os

from pyparsejson.core.flow import Flow
from pyparsejson.core.repair import Repair
from pyparsejson.core.rule_selector import RuleSelector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyparsejson.report.repair_report import RepairReport, RepairStatus

from pyparsejson.rules.values.literals import QuoteBareWordsRule


class MyBusinessFlow(Flow):
    def __init__(self, engine):
        super().__init__(engine)
        self.max_passes = 2
        self.selector = (
            RuleSelector()
            .add_tags("structure")
            .add_rules(QuoteBareWordsRule)
            # .exclude_rules(SomeDangerousRule)
        )

    def execute(self, context):
        return self.run(context)


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_report(input_text: str, report: RepairReport):
    print(f"\n{Colors.CYAN}► INPUT:{Colors.ENDC}")
    print(input_text.strip())

    status_color = Colors.GREEN if report.success else Colors.FAIL
    print(f"\n{Colors.BOLD}► ESTADO:{Colors.ENDC} {status_color}{report.status.name}{Colors.ENDC}")
    print(f"► REGLAS APLICADAS: {len(report.applied_rules)}")
    print(f"► ITERACIONES: {report.iterations}")
    print(f"► QUALITY SCORE: {report.quality_score}")

    if report.success:
        print(f"\n{Colors.GREEN}► JSON FINAL:{Colors.ENDC}")
        print(report.json_text)
    else:
        print(f"\n{Colors.FAIL}► ERROR:{Colors.ENDC}")
        print(report.errors[-1] if report.errors else "Unknown error")
        print(f"\n{Colors.WARNING}► INTENTO DE REPARACIÓN:{Colors.ENDC}")
        print(report.json_text)


def run_case(title: str, text: str, pipeline: Repair):
    print(f"\n{Colors.HEADER}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'═' * 60}{Colors.ENDC}")
    report = pipeline.parse(text)
    print_report(text, report)


def run_demo():
    print(f"{Colors.BOLD}PYPARSEJSON - BATERÍA DE PRUEBAS EXTENDIDA{Colors.ENDC}")

    # Pipeline de producción con todos los flujos
    pipeline = Repair(auto_flows=True)

    # =================================================================
    # GRUPO 1: FUNDAMENTOS (JSON Minimo)
    # =================================================================
    run_case(
        "CASO 1: Pares sueltos simples",
        'user: "admin", active: si',
        pipeline
    )

    run_case(
        "CASO 2: Igual en vez de dos puntos",
        'user=admin, active=no',
        pipeline
    )

    run_case(
        "CASO 3: Sin comas entre claves",
        '''
        user: admin
        active: si
        role: superuser
        ''',
        pipeline
    )

    # =================================================================
    # GRUPO 2: TIPOS DE DATOS Y COMILLAS
    # =================================================================
    run_case(
        "CASO 4: Booleanos y números mixtos",
        'enabled: true, retries: 3, timeout: 10.5',
        pipeline
    )

    run_case(
        "CASO 5: Notación Científica",
        'avogadro: 6.022e23, planck: 6.626e-34',
        pipeline
    )

    run_case(
        "CASO 6: Fechas como números (Smart Typing)",
        'start_date: 2026-01-01, zip_code: 00851, phone: 555-0199',
        pipeline
    )

    run_case(
        "CASO 7: Comillas simples",
        "name: 'John Doe', role: 'admin'",
        pipeline
    )

    run_case(
        "CASO 8: Unicode y Acentos",
        'nombre: "François", país: "España"',
        pipeline
    )

    # =================================================================
    # GRUPO 3: ESTRUCTURAS ANIDADAS
    # =================================================================
    run_case(
        "CASO 9: Tuplas como listas",
        'permissions: (read, write, execute)',
        pipeline
    )

    run_case(
        "CASO 10: Objetos anidados profundos",
        '''
        user: {
            profile: {
                name: "Alice",
                age: 30,
                address: {
                    street: "Main St",
                    number: 123
                }
            }
        }
        ''',
        pipeline
    )

    run_case(
        "CASO 11: Lista de Objetos",
        'items: [ {id: 1, name: "A"}, {id: 2, name: "B"} ]',
        pipeline
    )

    run_case(
        "CASO 12: Mezcla de listas y objetos",
        'data: [1, "dos", true, {key: value}]',
        pipeline
    )

    run_case(
        "CASO 13: Arrays sin corchetes (implícitos)",
        'ids: 1, 2, 3, 4, 5',
        pipeline
    )

    # =================================================================
    # GRUPO 4: FRANKENSTEINS SINTÁCTICOS
    # =================================================================
    run_case(
        "CASO 14: Trailing Commas (JSON5)",
        '{data: [1, 2, 3, ], status: ok,}',
        pipeline
    )

    run_case(
        "CASO 15: Objeto sin root brackets",
        '''
        id: 1
        profile: { name: John, age: 30 }
        active: si
        ''',
        pipeline
    )

    run_case(
        "CASO 16: El clásico config file",
        '''
        user_id=998877
        preferences: {
            theme: dark,
            notifications: (email, sms)
        }
        verified: si
        ''',
        pipeline
    )

    run_case(
        "CASO 17: Todo en una línea, sin espacios",
        'user_id=998877 preferences:{theme:dark,notifications:(email,sms)} verified:si',
        pipeline
    )

    run_case(
        "CASO 18: Mezcla extrema de separadores",
        '''
        bank=si
        cooperative:no
        voucher:1231235
        deposito fecha='2026-01-01'
        ''',
        pipeline
    )

    # =================================================================
    # GRUPO 5: CASOS LÍMITE Y RAREZAS
    # =================================================================
    run_case(
        "CASO 19: String vacío y Null",
        'name: "", bio: null',
        pipeline
    )

    run_case(
        "CASO 20: Booleanos como Strings vs Literales",
        'is_admin: "true", is_active: true',
        pipeline
    )

    run_case(
        "CASO 21: Números negativos",
        'balance: -500.50, offset: -10',
        pipeline
    )

    run_case(
        "CASO 22: Espacios extra alrededor de claves",
        '{  user  :  admin  ,  active  :  si  }',
        pipeline
    )

    run_case(
        "CASO 23: Lista vacía implícita",
        'list: []',
        pipeline
    )

    # =================================================================
    # GRUPO 6: CHAOS TOTAL (Logs y outputs raros)
    # =================================================================
    run_case(
        "CASO 24: Log de aplicación tipo SQL",
        'INSERT INTO users (id, name) VALUES (1, "Carlos")',
        pipeline
    )

    run_case(
        "CASO 25: URL y Rutas",
        'url: https://example.com/api, path: /var/www/html',
        pipeline
    )

    run_case(
        "CASO 26: Texto casi libre (No se puede arreglar)",
        'hola mundo esto no es json pero tiene clave:valor',
        pipeline
    )

    run_case(
        "CASO 27: JSON casi válido",
        '{"a":1,"b":2,}',
        pipeline
    )

    run_case(
        "CASO 28: Entrada vacía",
        '',
        pipeline
    )

    run_case(
        "CASO 29: Solo palabras sueltas",
        'esto no tiene nada',
        pipeline
    )

    run_case(
        "CASO 30: Comentarios C-style (Experimental/Posible fallo)",
        'user: admin // superuser\nactive: si',
        pipeline
    )

    # =================================================================
    # DEMO: DRY RUN (AUDITORÍA)
    # =================================================================
    print(f"\n{Colors.HEADER}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}CASO: DRY RUN (Auditoría){Colors.ENDC}")
    print(f"{Colors.HEADER}{'═' * 60}{Colors.ENDC}")

    frankenstein_text = 'user=admin, active: si, id=123'

    # Configuramos el pipeline en modo auditoría
    # Opción A: En el constructor
    audit_pipeline = Repair(auto_flows=True, dry_run=True)
    report = audit_pipeline.parse(frankenstein_text)

    # Opción B: Sobrescribiendo en el método (como vimos en el paso anterior)
    # report = pipeline.parse(frankenstein_text, dry_run=True)

    print(f"\n► INPUT: {frankenstein_text}")
    print(f"► REGISTRO DE MODIFICACIONES (Dry Run):")
    if not report.modifications:
        print("  (No se requirieron cambios)")
    else:
        for mod in report.modifications:
            print(f"  - Regla: {mod.rule_name}")
            # Imprimimos solo un poco del diff
            print(f"    Diff: {mod.diff_preview.replace(chr(10), ' ')}")

    print(f"\n► RESULTADO JSON (Simulado): {report.json_text}")
    print(f"► ÉXITO: {report.success}")


if __name__ == "__main__":
    try:
        os.system('')
    except Exception:
        pass

    run_demo()