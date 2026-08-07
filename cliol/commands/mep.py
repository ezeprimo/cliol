"""Comandos de dólar MEP: estimaciones, parámetros, validación (lectura) y compra."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.trading_gate import TradingGate

mep_app = typer.Typer(help="Dólar MEP: estimación y operatoria simplificada.", no_args_is_help=True)

ESTIMATE_COLUMNS = {
    "monto_pesos": "Pesos",
    "monto_dolares": "Dólares",
    "tipo_cambio": "Tipo de cambio",
    "comision": "Comisión",
    "impuestos": "Impuestos",
    "costo_total": "Costo total",
    "titulo_utilizado": "Título",
}
PARAMETERS_COLUMNS = {
    "id_tipo_operatoria": "Tipo",
    "nombre": "Nombre",
    "monto_minimo": "Mínimo",
    "monto_maximo": "Máximo",
    "horario_inicio": "Horario inicio",
    "horario_fin": "Horario fin",
    "disponible": "Disponible",
}
VALIDATION_COLUMNS = {"valido": "Válido", "mensaje": "Mensaje", "monto_ajustado": "Monto ajustado"}
RESULT_COLUMNS = {
    "ok": "OK",
    "numero_operacion": "Operación",
    "numero_operacion_compra": "Compra",
    "numero_operacion_venta": "Venta",
    "mensaje": "Mensaje",
}
ESTIMATE_SUGGESTION = (
    "Use 'cliol mep estimate-buy {monto}' para ver el costo estimado antes de operar."
)


@mep_app.command("estimate-buy")
def mep_estimate_buy(
    monto: float = typer.Argument(..., min=0, help="Monto en pesos a invertir"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Estima el costo de comprar dólar MEP."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_mep_buy_estimate", monto=monto)
    print(
        OutputFormatter.render(
            data,
            columns=ESTIMATE_COLUMNS,
        )
    )


@mep_app.command("estimate-sell")
def mep_estimate_sell(
    monto: float = typer.Argument(..., min=0, help="Monto en dólares a vender"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Estima el resultado de vender dólar MEP."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_mep_sell_estimate", monto=monto)
    print(OutputFormatter.render(data, columns=ESTIMATE_COLUMNS))


@mep_app.command("parameters")
def mep_parameters(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    op_type: int = typer.Option(1, "--type", help="Tipo de operatoria (default: 1)"),
):
    """Muestra los parámetros de la operatoria MEP."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_mep_parameters", id_tipo_operatoria=op_type)
    print(OutputFormatter.render(data, columns=PARAMETERS_COLUMNS))


@mep_app.command("validate")
def mep_validate(
    monto: float = typer.Argument(..., min=0, help="Monto en pesos a validar"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    op_type: int = typer.Option(1, "--type", help="Tipo de operatoria (default: 1)"),
):
    """Valida una operación MEP sin ejecutarla (no pide contraseña)."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("validate_mep_operation", monto=monto, id_tipo_operatoria=op_type)
    print(OutputFormatter.render(data, columns=VALIDATION_COLUMNS))


@mep_app.command("buy")
def mep_buy(
    monto: float = typer.Argument(..., min=0, help="Monto en pesos a convertir"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    op_type: int = typer.Option(1, "--type", help="Tipo de operatoria (default: 1)"),
):
    """Compra dólar MEP (requiere operatoria habilitada)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    print(ESTIMATE_SUGGESTION.format(monto=monto))
    gate = TradingGate(config)
    gate.check()
    gate.prompt_password()
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch("buy_mep_simplified", monto=monto, id_tipo_operatoria=op_type)
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))
