"""Punto de entrada de cliol: árbol Typer con la CLI completa."""

import sys
import traceback

import typer

from cliol import __version__
from cliol.commands.advisor import advisor_app
from cliol.commands.auth import auth_app
from cliol.commands.config_cmd import config_app
from cliol.commands.cpd import cpd_app
from cliol.commands.fci import fci_app
from cliol.commands.market import market_app
from cliol.commands.mep import mep_app
from cliol.commands.portfolio import (
    account_app,
    operations_app,
    portfolio_app,
    profile_command,
)
from cliol.commands.security_cmd import security_app
from cliol.commands.setup import setup as setup_command
from cliol.commands.trading import trading_app
from cliol.errors import CliolError
from cliol.output import get_debug

__all__ = ["app", "run"]

VERSION_MESSAGE = f"cliol {__version__}"


app = typer.Typer(
    help="CLI para operar en Invertir Online desde la terminal.",
    no_args_is_help=True,
    add_completion=True,
)


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(False, "--version", help="Muestra la versión y sale."),
):
    """CLI para operar en Invertir Online desde la terminal."""
    if version:
        print(VERSION_MESSAGE)
        raise typer.Exit()


app.command(name="setup", help="Configura credenciales e ingreso de cliol.")(setup_command)
app.add_typer(auth_app, name="auth")
app.add_typer(config_app, name="config")
app.add_typer(security_app, name="security")
app.add_typer(market_app, name="market")
app.add_typer(portfolio_app, name="portfolio")
app.add_typer(account_app, name="account")
app.add_typer(operations_app, name="operations")
app.add_typer(fci_app, name="fci")
app.add_typer(mep_app, name="mep")
app.add_typer(cpd_app, name="cpd")
app.add_typer(trading_app, name="trading")
app.add_typer(advisor_app, name="advisor")
app.command(name="profile", help="Consulta el perfil del cliente.")(profile_command)


_app_called = False


def run() -> None:
    """Entry point de consola: enruta errores de dominio a stderr con código de salida."""
    global _app_called
    if _app_called:
        import sys
        print("[cliol] WARNING: run() called twice, skipping second invocation", file=sys.stderr)
        return
    _app_called = True
    try:
        app()
    except CliolError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except typer.Exit as exc:
        raise SystemExit(exc.exit_code or 0) from exc
    except KeyboardInterrupt:
        print("Interrumpido.", file=sys.stderr)
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        if get_debug():
            traceback.print_exc()
        else:
            print(f"Error inesperado: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    run()
