"""Constantes de cliol derivadas de las constantes de py_iol.

Los valores de py_iol son clases planas (no Enum). Este módulo las convierte
en listas canónicas para usar con opciones de Typer y provee un normalizador
de opciones sin distinción de mayúsculas/minúsculas.
"""

from pyIol import (
    Countries,
    CPDSegments,
    CPDStates,
    Markets,
    OperationStates,
    SettlementTerms,
)

__all__ = [
    "MARKETS",
    "SETTLEMENT_TERMS",
    "COUNTRIES",
    "CPD_STATES",
    "CPD_SEGMENTS",
    "OPERATION_STATES",
    "normalize_choice",
]


def _values(cls) -> list:
    """Valores de cadena de una clase constante py_iol, en orden de definición.

    Filtra: solo atributos que no son dunder, no tienen espacios (no son docstrings),
    y son strings. Esto excluye __module__, __doc__, y docstrings de clase.
    """
    return [
        v
        for k, v in vars(cls).items()
        if isinstance(v, str) and not k.startswith("__") and " " not in v
    ]


MARKETS = _values(Markets)
SETTLEMENT_TERMS = _values(SettlementTerms)
COUNTRIES = _values(Countries)
CPD_STATES = _values(CPDStates)
CPD_SEGMENTS = _values(CPDSegments)
OPERATION_STATES = _values(OperationStates)

DEFAULT_MARKET = MARKETS[0]  # bCBA
DEFAULT_SETTLEMENT_TERM = SETTLEMENT_TERMS[1]  # t1
DEFAULT_COUNTRY = COUNTRIES[0]  # argentina


def normalize_choice(value: str, choices: list) -> str:
    """Devuelve la variante canónica de `choices` que coincide sin distinguir mayúsculas.

    Devuelve None si no hay coincidencia.
    """
    if value is None:
        return None
    lowered = value.lower()
    for choice in choices:
        if choice.lower() == lowered:
            return choice
    return None
