"""Comandos `cliol security`: ciclo de vida de la contraseña de gastos."""

import typer

from cliol.config import ConfigManager
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.prompts import ask_password, confirm
from cliol.security import SpendingPassword

security_app = typer.Typer(help="Contraseña de gastos para operar.", no_args_is_help=True)

ALREADY_EXISTS = "Ya existe una contraseña de gastos. Use 'cliol security change-password' para modificarla."
NOT_SET_YET = "No existe una contraseña de gastos. Use 'cliol security set-password'."
SET_OK = "Contraseña de gastos configurada."
CHANGE_OK = "Contraseña de gastos actualizada."
CLEAR_OK = "Contraseña de gastos eliminada. Modo operatoria deshabilitado."
NO_PASSWORD_CONFIGURED = "No hay una contraseña de gastos configurada."


def _read_new_password(prompt_text: str, retry: bool = True) -> str:
    while True:
        first = ask_password(prompt_text)
        second = ask_password("Repetir contraseña de gastos")
        if first != second:
            if not retry:
                raise CliolError("Las contraseñas no coinciden.")
            print("Las contraseñas no coinciden, intente nuevamente.")
            continue
        try:
            return SpendingPassword.create(first)
        except ValueError as exc:
            raise CliolError(str(exc)) from exc


@security_app.command("set-password")
def set_password(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Crea la contraseña de gastos (mínimo 4 caracteres, enmascarada, confirmada)."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    if manager.get_password_hash() is not None:
        raise CliolError(ALREADY_EXISTS)
    hashed = _read_new_password("Nueva contraseña de gastos (mínimo 4 caracteres)")
    manager.set("trading.password_hash", hashed)
    print(SET_OK)


@security_app.command("change-password")
def change_password(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Cambia la contraseña de gastos (requiere la actual)."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    current_hash = manager.get_password_hash()
    if current_hash is None:
        raise CliolError(NOT_SET_YET)
    current = ask_password("Contraseña de gastos actual")
    try:
        new_hash = SpendingPassword.change(
            current, _read_new_password("Nueva contraseña de gastos"), current_hash
        )
    except ValueError as exc:
        raise CliolError(str(exc)) from exc
    manager.set("trading.password_hash", new_hash)
    print(CHANGE_OK)


@security_app.command("clear-password")
def clear_password(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Elimina la contraseña de gastos y desactiva la operatoria."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    current = manager.get_password_hash()
    if current is None:
        raise CliolError(NO_PASSWORD_CONFIGURED)
    if not confirm("¿Eliminar la contraseña de gastos? La operatoria quedará deshabilitada."):
        print("Operación cancelada.")
        return
    candidate = ask_password("Contraseña de gastos actual")
    if not SpendingPassword.verify(candidate, current):
        raise CliolError("Contraseña actual incorrecta.")
    config = manager.load()
    SpendingPassword.clear(config)
    config["trading"]["enabled"] = False
    manager.save(config)
    print(CLEAR_OK)
