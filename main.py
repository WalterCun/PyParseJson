import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyparsejson.core.pipeline import Pipeline
from pyparsejson.report.repair_report import RepairReport, RepairStatus

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
    print(f"\n{Colors.CYAN}► INPUT:{Colors.ENDC} {input_text.strip()[:60]}...")
    
    status_color = Colors.GREEN if report.success else Colors.FAIL
    print(f"{Colors.BOLD}► ESTADO:{Colors.ENDC} {status_color}{report.status.name}{Colors.ENDC}")
    print(f"► REGLAS APLICADAS: {len(report.applied_rules)} {report.applied_rules}")
    print(f"► ITERACIONES: {report.iterations}")
    
    if report.success:
        print(f"{Colors.GREEN}► JSON:{Colors.ENDC} {report.json_text}")
    else:
        print(f"{Colors.FAIL}► ERROR:{Colors.ENDC} {report.errors[-1] if report.errors else 'Unknown'}")
        print(f"{Colors.WARNING}► INTENTO:{Colors.ENDC} {report.json_text}")

def run_demo():
    print(f"{Colors.BOLD}PYPARSEJSON - DEMO INCREMENTAL REAL{Colors.ENDC}")
    
    pipeline = Pipeline()
    
    # Caso 1: Reparación Exitosa (Pares sueltos)
    text_success = 'user: "admin", active: si'
    print(f"\n{Colors.HEADER}CASO 1: Pares Sueltos (WrapRootObject){Colors.ENDC}")
    report = pipeline.parse(text_success)
    print_report(text_success, report)
    
    # Caso 2: Frankenstein
    text_frank = """
    user_id=998877
    preferences: {
        theme: dark,
        notifications: (email, sms)
    }
    verified: si
    """
    print(f"\n{Colors.HEADER}CASO 2: Frankenstein{Colors.ENDC}")
    report = pipeline.parse(text_frank)
    print_report(text_frank, report)

if __name__ == "__main__":
    try:
        os.system('')
    except:
        pass
    run_demo()
