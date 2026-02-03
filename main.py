"""
Script de demostración y banco de pruebas para la librería PyParseJson.

Este archivo contiene una serie de casos de prueba diseñados para mostrar
las capacidades de reparación de la librería, desde JSONs casi válidos hasta
entradas de texto muy corruptas.

El script ejecuta cada caso a través del pipeline de reparación estándar y luego
imprime un informe detallado de los resultados, separando los casos exitosos
de los fallidos.
"""

from pyparsejson.core.repair import Repair
from pyparsejson.report.repair_report import RepairReport

case: list = []

class Colors:
    """Clase de utilidad para imprimir texto con colores en la terminal."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_report(title: str, input_text: str, report: RepairReport):
    """
    Imprime un informe formateado para un único caso de prueba.

    Args:
        title: El título del caso de prueba.
        input_text: El texto de entrada original que se intentó reparar.
        report: El objeto RepairReport generado por el pipeline.
    """
    print(f"\n{Colors.HEADER}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'═' * 60}{Colors.ENDC}")

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


def run_case(title: str, text: str, pipeline: Repair) -> tuple[str, str, RepairReport]:
    """
    Ejecuta un único caso de prueba a través del pipeline de reparación.

    Args:
        title: El título descriptivo del caso.
        text: El string de entrada a reparar.
        pipeline: La instancia del reparador a utilizar.

    Returns:
        Una tupla con el título, el texto original y el reporte generado.
    """
    report = pipeline.parse(text)
    return title, text, report


def run_demo():
    """
    Función principal que ejecuta la batería completa de casos de prueba.
    """
    print(f"{Colors.BOLD}PYPARSEJSON - BATERÍA DE PRUEBAS EXTENDIDA{Colors.ENDC}")
    results = []
    pipeline = Repair(debug=True)

    # =================================================================
    # GRUPO 1: FUNDAMENTOS (JSON Mínimo)
    # =================================================================
    results.append(run_case("CASO 1: Pares sueltos simples", 'user: "admin", active: si', pipeline))
    results.append(run_case("CASO 2: Igual en vez de dos puntos", 'user=admin, active=no', pipeline))
    results.append(run_case("CASO 3: Sin comas entre claves", '''user: admin active: si role: superuser ''', pipeline))
    # =================================================================
    # GRUPO 2: TIPOS DE DATOS Y COMILLAS
    # =================================================================
    results.append(run_case("CASO 4: Booleanos y números mixtos", 'enabled: true, retries: 3, timeout: 10.5', pipeline))
    results.append(run_case("CASO 5: Notación Científica", 'avogadro: 6.022e23, planck: 6.626e-34', pipeline))
    results.append(run_case("CASO 6: Fechas como números (Smart Typing)",
                            'start_date: 2026-01-01, zip_code: 00851, phone: 555-0199', pipeline))
    results.append(run_case("CASO 7: Comillas simples", "name: 'John Doe', role: 'admin'", pipeline))
    results.append(run_case("CASO 8: Unicode y Acentos", 'nombre: "François", país: "España"', pipeline))
    # =================================================================
    # GRUPO 3: ESTRUCTURAS ANIDADAS
    # =================================================================
    results.append(run_case("CASO 9: Tuplas como listas", 'permissions: (read, write, execute)', pipeline))
    results.append(run_case(
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
    ))
    results.append(run_case("CASO 11: Lista de Objetos", 'items: [ {id: 1, name: "A"}, {id: 2, name: "B"} ]', pipeline))
    results.append(run_case("CASO 12: Mezcla de listas y objetos", 'data: [1, "dos", true, {key: value}]', pipeline))
    results.append(run_case("CASO 13: Arrays sin corchetes (implícitos)", 'ids: 1, 2, 3, 4, 5', pipeline))
    # =================================================================
    # GRUPO 4: FRANKENSTEINS SINTÁCTICOS
    # =================================================================
    results.append(run_case("CASO 14: Trailing Commas (JSON5)", '{data: [1, 2, 3, ], status: ok,}', pipeline))
    results.append(run_case(
        "CASO 15: Objeto sin root brackets",
        '''
        id: 1
        profile: { name: John, age: 30 }
        active: si
        ''',
        pipeline
    ))
    results.append(run_case(
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
    ))
    results.append(run_case(
        "CASO 17: Todo en una línea, sin espacios",
        'user_id=998877 preferences:{theme:dark,notifications:(email,sms)} verified:si',
        pipeline
    ))
    results.append(run_case(
        "CASO 18: Mezcla extrema de separadores",
        '''
        bank=si
        cooperative:no
        voucher:1231235
        deposito fecha='2026-01-01'
        ''',
        pipeline
    ))
    # =================================================================
    # GRUPO 5: CASOS LÍMITE Y RAREZAS
    # =================================================================
    results.append(run_case("CASO 19: String vacío y Null", 'name: "", bio: null', pipeline))
    results.append(
        run_case("CASO 20: Booleanos como Strings vs Literales", 'is_admin: "true", is_active: true', pipeline))
    results.append(run_case("CASO 21: Números negativos", 'balance: -500.50, offset: -10', pipeline))
    results.append(
        run_case("CASO 22: Espacios extra alrededor de claves", '{  user  :  admin  ,  active  :  si  }', pipeline))
    results.append(run_case("CASO 23: Lista vacía implícita", 'list: []', pipeline))
    # =================================================================
    # GRUPO 6: CHAOS TOTAL (Logs y outputs raros)
    # =================================================================
    results.append(
        run_case("CASO 24: Log de aplicación tipo SQL", 'INSERT INTO users (id, name) VALUES (1, "Carlos")', pipeline))
    results.append(run_case("CASO 25: URL y Rutas", 'url: https://example.com/api, path: /var/www/html', pipeline))
    results.append(run_case("CASO 26: Texto casi libre (No se puede arreglar)",
                            'hola mundo esto no es json pero tiene clave:valor', pipeline))
    results.append(run_case("CASO 27: JSON casi válido", '{"a":1,"b":2,}', pipeline))
    results.append(run_case("CASO 28: Entrada vacía", '', pipeline))
    results.append(run_case("CASO 29: Solo palabras sueltas", 'esto no tiene nada', pipeline))
    results.append(
        run_case("CASO 30: Comentarios C-style (Experimental/Posible fallo)", 'user: admin\nactive: si',
                 pipeline))
    results.append(run_case("CASO 31: Textos largos (Experimental/Posible fallo)",
                            'user: este es un usuario administrador el cual debe estar siempre activo,active: si',
                            pipeline))
    results.append(run_case("CASO 32: Texto Real 1", """{
breakfast:1,
parking:1,
final_consumer_invoice:0316513653216,
foreigner:0,
}""",pipeline))
    results.append(run_case("CASO 33: Texto Real 2", """{
bank:0
cooperative:0
voucher:1
deposit_date:01-01-2026
}""",pipeline))


    # =================================================================
    # DEMO: DRY RUN (AUDITORÍA)
    # =================================================================
    frankenstein_text = 'user=admin, active: si, id=123'
    audit_pipeline = Repair(auto_flows=True, dry_run=True)
    results.append(run_case(
        "CASO DRY RUN (Auditoría)",
        frankenstein_text,
        audit_pipeline
    ))

    success_reports = [(t, txt, r) for t, txt, r in results if r.success]
    failed_reports = [(t, txt, r) for t, txt, r in results if not r.success]

    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ CASOS EXITOSOS ({len(success_reports)}){Colors.ENDC}")
    for title, text, report in success_reports:
        print_report(title, text, report)

    print(f"\n{Colors.FAIL}{Colors.BOLD}❌ CASOS CON ERROR ({len(failed_reports)}){Colors.ENDC}")
    for title, text, report in failed_reports:
        print_report(title, text, report)

    print(f"""
    {Colors.BOLD}📊 RESUMEN FINAL{Colors.ENDC}
    ------------------------------------
    Total casos     : {len(results)} 
    Exitosos        : {len(success_reports)}
    Fallidos        : {len(failed_reports)}
    Ratio éxito     : {len(success_reports) / len(results):.2%}
    """)


if __name__ == "__main__":
    try:
        # Habilita el soporte de colores ANSI en terminales de Windows
        import os

        os.system('')
    except Exception as e:
        print(f"Error: {e}")

    run_demo()
