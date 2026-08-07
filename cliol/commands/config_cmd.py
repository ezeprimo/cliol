"""Comando `cliol config`: lectura/escritura de valores y modo operatoria."""

import typer

from cliol.config import ConfigManager
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.prompts import confirm
from cliol.security import SpendingPassword

config_app = typer.Typer(help="Lee y escribe la configuración de cliol.", no_args_is_help=True)
trading_app = typer.Typer(
    help="Activa, desactiva o consulta el modo operatoria.", no_args_is_help=True
)

ENABLE_NO_PASSWORD = (
    "Debe configurar una contraseña de gastos primero. Use 'cliol security set-password'."
)
ENABLED_MESSAGE = "Modo operatoria habilitado."
ALREADY_ENABLED_MESSAGE = "El modo operatoria ya está habilitado."
ALREADY_DISABLED_MESSAGE = "El modo operatoria ya está deshabilitado."
DISABLED_CLEARED_MESSAGE = "Modo operatoria deshabilitado. Contraseña de gastos eliminada."
STATUS_ENABLED = "Modo operatoria: HABILITADO"
STATUS_DISABLED = "Modo operatoria: DESHABILITADO (solo consulta)"


def _mask(value: str, key: str) -> str:
    if key in ConfigManager.PASSWORD_KEYS:
        return ConfigManager.MASK
    return value


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Clave con puntos, ej: iol.username"),
    value: str = typer.Argument(..., help="Valor a guardar"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Guarda una clave de configuración."""
    output_flags(json, csv, verbose, debug)
    ConfigManager().set(key, value)
    print(_mask(value, key))


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Clave con formato, ej: iol.username"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Muestra el valor de una clave (las contraseñas se muestran enmascaradas)."""
    output_flags(json, csv, verbose, debug)
    value = ConfigManager().get(key)
    print(_mask(value, key))


@config_app.command("list")
def config_list(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Lista todas las claves y valores (contraseñas enmascaradas)."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    config = manager.load()
    pairs = manager.dotted_pairs(config)
    data = [{"clave": key, "valor": _mask(str(value), key)} for key, value in pairs]
    print(OutputFormatter.render(data, columns={"clave": "Clave", "valor": "Valor"}))


@trading_app.command("enable")
def trading_enable(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Activa la operatoria (requiere contraseña de gastos configurada)."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    if manager.get_password_hash() is None:
        raise CliolError(ENABLE_NO_PASSWORD)
    if manager.is_trading_enabled():
        print(ALREADY_ENABLED_MESSAGE)
        return
    manager.set("trading.enabled", "true")
    print(ENABLED_MESSAGE)


@trading_app.command("disable")
def trading_disable(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Desactiva el modo operatoria y elimina la contraseña de gastos."""
    output_flags(json, csv, verbose, debug)
    manager = ConfigManager()
    if not manager.is_trading_enabled():
        print(ALREADY_DISABLED_MESSAGE)
        return
    if not confirm(f"¿Desactivar el modo operatoria? {DISABLED_CLEARED_MESSAGE}"):
        print("Operación cancelada.")
        return
    config = manager.load()
    SpendingPassword.clear(config)
    config["trading"]["enabled"] = False
    manager.save(config)
    print(DISABLED_CLEARED_MESSAGE)


@trading_app.command("status")
def trading_status(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Muestra si el modo operatoria está habilitado o no."""
    output_flags(json, csv, verbose, debug)
    status = STATUS_ENABLED if ConfigManager().is_trading_enabled() else STATUS_DISABLED
    print(status)


config_app.add_typer(trading_app, name="trading")
