import json
from typing import TextIO, Any, Optional

# Importamos los componentes internos necesarios
from pyparsejson.core.repair import Repair
from pyparsejson.core.flow import Flow
from pyparsejson.report.repair_report import RepairStatus

__version__ = "0.2.0"


def loads(text: str, *, auto_flows: bool = True, flow: Optional[Flow] = None) -> Any:
    """
    Deserializa `text` (un string que contiene un documento JSON posiblemente roto)
    a un objeto Python.

    Esta función es un reemplazo directo para `json.loads()`.
    Si el input no es JSON válido, intentará repararlo antes de fallar.

    Args:
        text: El string con el JSON (o "Frankenstein JSON") a parsear.
        auto_flows: Si es True (default), usa los flujos estándar de reparación.
        flow: Una instancia de Flow personalizada para sobrescribir el comportamiento.

    Returns:
        El objeto Python resultante (dict, list, etc).

    Raises:
        json.JSONDecodeError: Si incluso después de intentar repararlo, el texto no es válido.
    """
    if not isinstance(text, str):
        # Intento de compatibilidad con json.loads que también acepta bytes
        text = text.decode('utf-8')

    # Inicializamos el motor de reparación
    pipeline = Repair(auto_flows=auto_flows)

    # Si el usuario proveyó un flujo personalizado, lo añadimos
    if flow:
        pipeline.add_flow(flow)

    # Ejecutamos el parsing
    report = pipeline.parse(text)

    if report.success:
        return report.python_object
    else:
        # Si fallamos, lanzamos la excepción estándar de Python para mantener compatibilidad
        # con bloques try/except existentes en otros proyectos.
        error_msg = report.errors[-1] if report.errors else "Unknown unrecoverable error"
        raise json.JSONDecodeError(
            msg=f"PyParseJson failed to repair input: {error_msg}",
            doc=text,
            pos=0
        )


def load(fp: TextIO, *, auto_flows: bool = True, flow: Optional[Flow] = None) -> Any:
    """
    Deserializa `fp` (un archivo .read() soportado) a un objeto Python.

    Esta función es un reemplazo directo para `json.load()`.
    """
    text = fp.read()
    return loads(text, auto_flows=auto_flows, flow=flow)


def __getattr__(name):
    """
    Proxy para permitir que el usuario importe excepciones o constantes
    directamente desde pyparsejson si lo desea, aunque delegamos a json.
    """
    if name == "JSONDecodeError":
        return json.JSONDecodeError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")