"""Comandos de CPD (cheques de pago diferido): lectura y compra."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.constants import CPD_SEGMENTS, CPD_STATES, normalize_choice
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.trading_gate import TradingGate

cpd_app = typer.Typer(help="Cheques de pago diferido (CPD).", no_args_is_help=True)

CPD_COLUMNS = {
    "numero_cheque": "Cheque",
    "librador": "Librador",
    "importe": "Importe",
    "tasa": "Tasa %",
    "plazo": "Plazo",
    "segmento": "Segmento",
    "estado": "Estado",
    "fecha_vencimiento": "Vencimiento",
}
COMMISSIONS_COLUMNS = {
    "comision": "Comisión",
    "iva_comision": "IVA comisión",
    "derechos_mercado": "Derechos",
    "iva_derechos": "IVA derechos",
    "total_gastos": "Total gastos",
}
RESULT_COLUMNS = {
    "ok": "OK",
    "numero_operacion": "Operación",
    "numero_cheque": "Cheque",
    "importe": "Importe",
    "precio": "Precio",
    "mensaje": "Mensaje",
}
CAN_OPERATE = "Cuenta habilitada para operar CPD."
CANNOT_OPERATE = "Cuenta no habilitada para operar CPD."
SUGGESTION = "Use 'cliol cpd commissions' para ver las comisiones antes de operar."


def _resolve(value, choices, kind) -> str:
    canonical = normalize_choice(value, choices)
    if canonical is None:
        raise CliolError(f"{kind} inválido: {value}. Valores válidos: {', '.join(choices)}")
    return canonical


@cpd_app.command("can-operate")
def cpd_can_operate(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Verifica si la cuenta puede operar CPD."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("can_operate_cpd")
    if data.puede_operar if hasattr(data, "puede_operar") else data.get("puedeOperar", True):
        print(CAN_OPERATE)
        return
    reason = getattr(data, "motivo", None) or getattr(data, "mensaje", "") or ""
    print(f"{CANNOT_OPERATE}: {reason}" if reason else CANNOT_OPERATE)


@cpd_app.command("list")
def cpd_list(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    state: str = typer.Option("vigentes", "--state", help="Estado (vigentes|vencidos|todos)"),
    segment: str = typer.Option(
        "avalados", "--segment", help="Segmento (avalados|patrocinados|garantizados|todos)"
    ),
):
    """Lista cheques con filtros por estado y segmento."""
    output_flags(json, csv, verbose, debug)
    estado = _resolve(state, CPD_STATES, "Estado")
    segmento = _resolve(segment, CPD_SEGMENTS, "Segmento")
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_cpd_list", estado=estado, segmento=segmento)
    print(OutputFormatter.render(data, columns=CPD_COLUMNS))


@cpd_app.command("commissions")
def cpd_commissions(
    importe: float = typer.Argument(..., help="Importe del cheque"),
    plazo: int = typer.Argument(..., help="Plazo en días"),
    tasa: float = typer.Argument(..., help="Tasa anual en %"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Calcula las comisiones de una operación CPD."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_cpd_commissions", importe=importe, plazo=plazo, tasa=tasa)
    print(OutputFormatter.render(data, columns=COMMISSIONS_COLUMNS))


@cpd_app.command("buy")
def cpd_buy(
    cheque_number: str = typer.Argument(..., help="Número del cheque, ej: CH-12345"),
    price: float = typer.Argument(..., min=0, help="Precio de compra"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    quantity: int = typer.Option(1, "--quantity", help="Cantidad de cheques (default: 1)"),
):
    """Compra un cheque de pago diferido (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    print(SUGGESTION)
    config = ConfigManager()
    gate = TradingGate(config)
    gate.check()
    gate.prompt_password()
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "operate_cpd", numero_cheque=cheque_number, precio=price, cantidad=quantity
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))
