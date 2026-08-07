"""Opciones globales de cliol compartidas por todos los comandos.

Cada comando declara las cuatro banderas (--json/--csv/--verbose/--debug)
usando estas constantes para que aparezcan en su ayuda y se sincronicen con
el estado global de salida (ver cliol.output).
"""

import typer

from cliol.errors import CliolError
from cliol.output import set_debug, set_format, set_verbose

__all__ = [
    "JSON_OPTION",
    "CSV_OPTION",
    "VERBOSE_OPTION",
    "DEBUG_OPTION",
    "output_flags",
]

JSON_OPTION = typer.Option(False, "--json", is_flag=True, help="Salida como JSON.")
CSV_OPTION = typer.Option(False, "--csv", is_flag=True, help="Salida como CSV.")
VERBOSE_OPTION = typer.Option(
    False, "--verbose", is_flag=True, help="Imprimir contexto adicional en stderr."
)
DEBUG_OPTION = typer.Option(
    False, "--debug", is_flag=True, help="Imprimir detalles de depuración y trazas."
)


def output_flags(json: bool, csv: bool, verbose: bool, debug: bool) -> None:
    """Sincroniza las banderas globales con el estado de salida del módulo."""
    if json and csv:
        raise CliolError("Only one output format allowed")
    set_format("json" if json else "csv" if csv else "table")
    set_verbose(verbose)
    set_debug(debug)
