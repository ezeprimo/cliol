"""Comandos de operación: comprar/vender acciones y bonos, cancelar. Requieren operatoria."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.constants import MARKETS, SETTLEMENT_TERMS, normalize_choice
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.trading_gate import TradingGate

trading_app = typer.Typer(
    help="Comprar, vender y cancelar órdenes (requiere operatoria habilitada).",
    no_args_is_help=True,
)

RESULT_COLUMNS = {"ok": "OK", "numero_operacion": "Operación", "mensaje": "Mensaje"}
OPERATION_HINT = "Orden: {action} {cantidad} x {symbol} @ ${precio:.2f} = ${total:,.2f} (mercado: {market}, plazo: {term})"
CANCELLED_MESSAGE = "Operación {numero} cancelada."


def _resolve_choice(value, choices, kind) -> str:
    canonical = normalize_choice(value, choices)
    if canonical is None:
        raise CliolError(f"{kind} inválido: {value}. Valores válidos: {', '.join(choices)}")
    return canonical


def _gate(config) -> TradingGate:
    """Creates ONE gate instance, calls both check() and prompt_password() on it."""
    gate = TradingGate(config)
    gate.check()
    gate.prompt_password()
    return gate


def _order_summary(action: str, cantidad: int, symbol: str, precio: float, market: str, term: str):
    total = cantidad * precio
    print(
        OPERATION_HINT.format(
            action=action,
            cantidad=cantidad,
            symbol=symbol,
            precio=precio,
            total=total,
            market=market,
            term=term,
        )
    )


@trading_app.command("buy")
def trading_buy(
    symbol: str = typer.Argument(..., help="Símbolo a comprar, ej: GGAL"),
    quantity: int = typer.Argument(..., min=1, help="Cantidad de títulos"),
    price: float = typer.Argument(..., min=0, help="Precio límite"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
    term: str = typer.Option("t1", "--term", help="Plazo de liquidación (default: t1)"),
    validity: str = typer.Option(None, "--validity", help="Validez de la orden (ISO8601)"),
):
    """Compra títulos en pesos (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    market = _resolve_choice(market, MARKETS, "Mercado")
    term = _resolve_choice(term, SETTLEMENT_TERMS, "Plazo")
    _order_summary("COMPRAR", quantity, symbol, price, market, term)
    config = ConfigManager()
    _gate(config)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "buy",
            simbolo=symbol,
            cantidad=quantity,
            precio=price,
            mercado=market,
            plazo=term,
            validez=validity,
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))


@trading_app.command("sell")
def trading_sell(
    symbol: str = typer.Argument(..., help="Símbolo a vender, ej: GGAL"),
    quantity: int = typer.Argument(..., min=1, help="Cantidad de títulos"),
    price: float = typer.Argument(..., min=0, help="Precio límite"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
    term: str = typer.Option("t1", "--term", help="Plazo de liquidación (default: t1)"),
    validity: str = typer.Option(None, "--validity", help="Validez de la orden (ISO8601)"),
):
    """Vende títulos en el mercado (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    market = _resolve_choice(market, MARKETS, "Mercado")
    term = _resolve_choice(term, SETTLEMENT_TERMS, "Plazo")
    _order_summary("VENDER", quantity, symbol, price, market, term)
    config = ConfigManager()
    _gate(config)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "sell",
            simbolo=symbol,
            cantidad=quantity,
            precio=price,
            mercado=market,
            plazo=term,
            validez=validity,
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))


@trading_app.command("buy-usd")
def trading_buy_usd(
    symbol: str = typer.Argument(..., help="Bono en especie D, ej: GD30"),
    quantity: int = typer.Argument(..., min=1, help="Cantidad (valor nominal)"),
    price: float = typer.Argument(..., min=0, help="Precio en dólares"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
    term: str = typer.Option("t1", "--term", help="Plazo (default: t1)"),
    validity: str = typer.Option(None, "--validity", help="Validez (ISO8601)"),
):
    """Compra bonos en especie D (dólares) — requiere operatoria."""
    output_flags(json, csv, verbose, debug)
    market = _resolve_choice(market, MARKETS, "Mercado")
    term = _resolve_choice(term, SETTLEMENT_TERMS, "Plazo")
    _order_summary("COMPRAR", quantity, symbol, price, market, term)
    config = ConfigManager()
    _gate(config)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "buy_dollar_bond",
            simbolo=symbol,
            cantidad=quantity,
            precio=price,
            mercado=market,
            plazo=term,
            validez=validity,
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))


@trading_app.command("sell-usd")
def trading_sell_usd(
    symbol: str = typer.Argument(..., help="Bono en especie, ej. GD30"),
    quantity: int = typer.Argument(..., min=1, help="Cantidad"),
    price: float = typer.Argument(..., min=0, help="Precio en dólares"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
    term: str = typer.Option("t1", "--term", help="Plazo (default: t1)"),
    validity: str = typer.Option(None, "--validity", help="Validez (ISO8601)"),
):
    """Vende bonos en dólares (especie D) — requiere operatoria."""
    output_flags(json, csv, verbose, debug)
    market = _resolve_choice(market, MARKETS, "Mercado")
    term = _resolve_choice(term, SETTLEMENT_TERMS, "Plazo")
    _order_summary("VENDER", quantity, symbol, price, market, term)
    config = ConfigManager()
    _gate(config)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "sell_dollar_bond",
            simbolo=symbol,
            cantidad=quantity,
            precio=price,
            mercado=market,
            plazo=term,
            validez=validity,
        )
    print(OutputFormatter.render(data, columns=RESULT_COLUMNS))


@trading_app.command("cancel")
def trading_cancel(
    numero: int = typer.Argument(..., help="Número de la operación a cancelar"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Cancela una operación pendiente — requiere operatoria."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    _gate(config)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        data = client.dispatch("cancel_operation", numero=numero)
    if data is True:
        print(CANCELLED_MESSAGE.format(numero=numero))
    else:
        print(OutputFormatter.render(data, columns=RESULT_COLUMNS))
