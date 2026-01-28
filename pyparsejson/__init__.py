"""
PyParseJson: Una librería robusta para reparar y parsear JSON mal formado.

Este módulo expone las funciones principales `load` y `loads`, diseñadas para ser
reemplazos directos (drop-in replacements) de las funciones estándar de `json`,
pero con capacidades avanzadas de recuperación de errores.
"""

import json
from typing import TextIO, Any, Optional

from pyparsejson.core.repair import Repair
from pyparsejson.core.flow import Flow
from pyparsejson.report.repair_report import RepairStatus

__version__ = "0.2.0"
__all__ = ["load", "loads", "Repair", "Flow", "RepairStatus", "JSONDecodeError"]


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
        try:
            text = text.decode('utf-8')
        except AttributeError:
            # Si no tiene decode, asumimos que ya es str o fallará más adelante
            pass

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

    Args:
        fp: Un objeto file-like que soporte .read().
        auto_flows: Si es True (default), usa los flujos estándar de reparación.
        flow: Una instancia de Flow personalizada.

    Returns:
        El objeto Python resultante.
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
