"""Comandos de FCI: listado/detalle (lectura) y suscripción/rescate (operatoria)."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.trading_gate import TradingGate

fci_app = typer.Typer(help="Fondos comunes de inversión.", no_args_is_help=True)

FCI_LIST_COLUMNS = {
    "simbolo": "Símbolo",
    "nombre": "Nombre",
    "administradora": "Administradora",
    "tipo_fondo": "Tipo",
    "moneda": "Moneda",
    "valor_cuotaparte": "Cuotaparte",
    "variacion_diaria": "Variación %",
}
FCI_DETAIL_COLUMNS = {
    "simbolo": "Símbolo",
    "nombre": "Nombre",
    "tipo_fondo": "Tipo",
    "moneda": "Moneda",
    "valor_cuotaparte": "Valor cuotaparte",
    "monto_minimo": "Mínimo",
    "rescate": "Plazo rescate",
    "perfil_inversor": "Perfil",
}
TYPES_COLUMNS = {"identificador": "ID", "nombre": "Nombre"}
MANAGERS_COLUMNS = {"id": "ID", "nombre": "Nombre", "descripcion": "Descripción"}
RESULT_COLUMNS = {
    "ok": "OK",
    "numero_operacion": "Operación",
    "mensaje": "Mensaje",
    "cuotapartes_estimadas": "Cuotapartes",
    "monto_estimado": "Monto USD/ARS",
}


@fci_app.command("list")
def fci_list(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Lista todos los fondos comunes de inversión."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_fci_list")
    print(
        OutputFormatter.render(data, columns=FCI_LIST_COLUMNS, color_columns=("variacion_diaria",))
    )


@fci_app.command("detail")
def fci_detail(
    symbol: str = typer.Argument(..., help="Símbolo del fondo, ej: AHORRO"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Detalle de un fondo."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_fci_detail", simbolo=symbol)
    print(OutputFormatter.render(data, columns=FCI_DETAIL_COLUMNS))


@fci_app.command("types")
def fci_types(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Lista los tipos de fondo."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_fci_types")
    print(OutputFormatter.render(data, columns=TYPES_COLUMNS))


@fci_app.command("managers")
def fci_managers(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Lista las administradoras de fondos con su código."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_fci_managers")
    print(OutputFormatter.render(data, columns=MANAGERS_COLUMNS))


@fci_app.command("types-by-manager")
def fci_types_by_manager(
    admin_code: str = typer.Argument(..., help="Código de administradora, ej: 3"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Lista los tipos de fondo de una administradora."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_fci_types_by_manager", administradora=admin_code)
    print(OutputFormatter.render(data, columns=TYPES_COLUMNS))


def _fci_gate(config, validate: bool):
    """Gate check + password prompt on a single TradingGate instance."""
    if validate:
        return
    gate = TradingGate(config)
    gate.check()
    gate.prompt_password()


@fci_app.command("subscribe")
def fci_subscribe(
    symbol: str = typer.Argument(..., help="Símbolo del fondo (ej: AHORRO)"),
    monto: float = typer.Argument(..., min=0, help="Monto en pesos a invertir"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    validate: bool = typer.Option(False, "--validate", help="Solo validar, sin ejecutar"),
):
    """Suscribe a un fondo común de inversión (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    _fci_gate(config, validate)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch("subscribe_fci", simbolo=symbol, monto=monto, solo_validar=validate)
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))


@fci_app.command("redeem")
def fci_redeem(
    symbol: str = typer.Argument(..., help="Símbolo del fondo (ej: AHORRO)"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    amount: float = typer.Option(None, "--amount", help="Monto en pesos a rescatar"),
    quantity: float = typer.Option(None, "--quantity", help="Cantidad de cuotapartes a rescatar"),
    validate: bool = typer.Option(False, "--validate", help="Solo validar, sin ejecutar"),
):
    """Rescata cuotapartes de un fondo (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    if amount is not None and quantity is not None:
        raise CliolError("Debe especificar solo --amount o --quantity, no ambos.")
    if amount is None and quantity is None:
        raise CliolError("Debe especificar --amount o --quantity.")
    config = ConfigManager()
    _fci_gate(config, validate)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "redeem_fci",
            simbolo=symbol,
            monto=amount,
            cantidad=quantity,
            solo_validar=validate,
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))
