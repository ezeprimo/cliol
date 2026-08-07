"""Comando `cliol auth test`: verifica las credenciales IOL."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.errors import AuthError, CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags

auth_app = typer.Typer(help="Verificación de credenciales de IOL.", no_args_is_help=True)

SUCCESS_MESSAGE = "Autenticación exitosa"
FAILURE_MESSAGE = "Error de autenticación: verifique usuario y contraseña"
UNCONFIGURED_MESSAGE = "Credenciales no configuradas. Ejecute 'cliol setup' primero."


@auth_app.command("test")
def auth_test(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Comprueba que las credenciales configuradas sean válidas."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    if not (config.load().get("iol") or {}).get("username"):
        raise CliolError(UNCONFIGURED_MESSAGE)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        if client.auth_test():
            print(SUCCESS_MESSAGE)
        else:
            raise AuthError(FAILURE_MESSAGE)
