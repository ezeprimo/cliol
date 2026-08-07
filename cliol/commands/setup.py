"""Comandos del grupo cliol (raíz): setup wizard."""

import typer

from cliol.config import ConfigManager
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.prompts import ask_password, ask_text, confirm
from cliol.security import SpendingPassword

setup_app = typer.Typer(
    help="Configuración inicial interactiva de cliol (credenciales IOL y operatoria).",
    no_args_is_help=True,
)

OVERWRITE_WARNING = "Ya existe una configuración. Se sobrescribirán las credenciales actuales."
TRADING_RISK_WARNING = (
    "AVISO: la operatoria REAL genera órdenes que impactan su cuenta de Invertir Online."
)
CONSULT_MODE_MESSAGE = (
    "Modo consulta activado. Puede habilitar operatoria luego con 'cliol config trading enable'."
)
SAVED_MESSAGE = "Configuración guardada."


def _read_credentials():
    username = ask_text("Usuario de IOL")
    password = ask_password("Contraseña de IOL")
    return username, password


def _read_spending_password():
    first = ask_password("Contraseña de gastos (mínimo 4 caracteres)")
    second = ask_password("Repetir contraseña de gastos")
    if first != second:
        raise CliolError("Las contraseñas no coinciden.")
    try:
        return SpendingPassword.create(first)
    except ValueError as exc:
        raise CliolError(str(exc)) from exc


@setup_app.command()
def setup(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Asistente de primera configuración (interactivo)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    if config.load():
        if not confirm(OVERWRITE_WARNING):
            print("Configuración no modificada.")
            return
    username, password = _read_credentials()
    print(TRADING_RISK_WARNING)
    enable_trading = confirm("¿Habilitar operatoria sobre su cuenta? (recomendado: NO)")
    trading = {"enabled": bool(enable_trading)}
    if enable_trading:
        trading["password_hash"] = _read_spending_password()
    config.save({"iol": {"username": username, "password": password}, "trading": trading})
    print(SAVED_MESSAGE)
    if not enable_trading:
        print(CONSULT_MODE_MESSAGE)
