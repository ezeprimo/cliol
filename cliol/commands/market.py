"""Comandos de mercado (solo consulta): cotizaciones, datos, opciones, paneles, MEP."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.constants import (
    COUNTRIES,
    MARKETS,
    SETTLEMENT_TERMS,
    normalize_choice,
)
from cliol.errors import APIError, CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter

market_app = typer.Typer(
    help="Datos de mercado: cotizaciones e instrumentos (solo consulta).", no_args_is_help=True
)

QUOTE_COLUMNS = {
    "simbolo": "Símbolo",
    "ultimo_precio": "Último",
    "variacion": "Variación %",
    "precio_compra": "Compra",
    "precio_venta": "Venta",
    "volumen_nominal": "Volumen",
    "fecha_hora": "Hora",
}
DATA_COLUMNS = {
    "simbolo": "Símbolo",
    "descripcion": "Descripción",
    "mercado": "Mercado",
    "moneda": "Moneda",
    "tipo": "Tipo",
    "plazo": "Plazo",
    "pais": "País",
}
OPTIONS_COLUMNS = {
    "simbolo": "Símbolo",
    "tipo_opcion": "Tipo",
    "fecha_vencimiento": "Vencimiento",
}
INSTRUMENTS_COLUMNS = {
    "instrumento": "Instrumento",
    "pais": "País",
}
MASSIVE_COLUMNS = {
    "simbolo": "Símbolo",
    "ultimo_precio": "Último",
    "variacion_porcentual": "Variación %",
    "volumen": "Volumen",
}
DETAIL_COLUMNS = {
    "simbolo": "Símbolo",
    "ultimo_precio": "Último",
    "variacion": "Variación %",
    "apertura": "Apertura",
    "maximo": "Máximo",
    "minimo": "Mínimo",
    "volumen_nominal": "Volumen",
    "monto_operado": "Monto",
}


def _resolve(value, choices, message_template) -> str:
    canonical = normalize_choice(value, choices)
    if canonical is None:
        raise CliolError(message_template.format(value=value, valid=", ".join(choices)))
    return canonical


def resolve_market(value: str) -> str:
    return _resolve(
        value,
        MARKETS,
        "Mercado inválido: {value}. Valores válidos: {valid}",
    )


def resolve_term(value: str) -> str:
    return _resolve(
        value,
        SETTLEMENT_TERMS,
        "Plazo inválido: {value}. Valores válidos: {valid}",
    )


def resolve_country(value: str) -> str:
    return _resolve(
        value,
        COUNTRIES,
        "País inválido: {value}. Valores válidos: {valid}",
    )


def _is_not_found(exc: Exception) -> bool:
    return "404" in str(exc)


@market_app.command("quote")
def market_quote(
    symbol: str = typer.Argument(..., help="Símbolo, ej: GGAL"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
    term: str = typer.Option("t1", "--term", help="Plazo de liquidación (default: t1)"),
):
    """Cotización en tiempo real de un título."""
    output_flags(json, csv, verbose, debug)
    market = resolve_market(market)
    term = resolve_term(term)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        try:
            data = client.dispatch(
                "get_stock_quote", symbol=symbol, market=market, settlement_term=term
            )
        except APIError as exc:
            if _is_not_found(exc):
                raise CliolError(
                    f"El símbolo '{symbol}' no fue encontrado en el mercado {market}."
                ) from exc
            raise
    # Inject symbol into result (py_iol models lack it); same shape for all formats
    rows = OutputFormatter.to_rows(data)
    if rows:
        rows[0]["simbolo"] = symbol.upper()
    print(OutputFormatter.render(rows, columns=QUOTE_COLUMNS, color_columns=("variacion",)))


@market_app.command("data")
def market_data(
    symbol: str = typer.Argument(..., help="Símbolo, ej: GGAL"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
):
    """Datos de un instrumento (metadata)."""
    output_flags(json, csv, verbose, debug)
    market = resolve_market(market)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_stock_data", symbol=symbol, market=market)
    rows = OutputFormatter.to_rows(data)
    if rows:
        rows[0]["simbolo"] = symbol.upper()
    print(OutputFormatter.render(rows, columns=DATA_COLUMNS))


@market_app.command("options")
def market_options(
    symbol: str = typer.Argument(..., help="Símbolo, ej: GGAL"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
):
    """Cadena de opciones de un título."""
    output_flags(json, csv, verbose, debug)
    market = resolve_market(market)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_stock_options", symbol=symbol, market=market)
    if not data:
        print(f"No se encontraron opciones para {symbol}.")
        return
    print(OutputFormatter.render(data, columns=OPTIONS_COLUMNS, color_columns=("variacion",)))


@market_app.command("instruments")
def market_instruments(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    country: str = typer.Option("argentina", "--country", help="País (default: argentina)"),
):
    """Lista los instrumentos de un país."""
    output_flags(json, csv, verbose, debug)
    country = resolve_country(country)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_market_instruments", pais=country)
    print(OutputFormatter.render(data, columns=INSTRUMENTS_COLUMNS))


@market_app.command("massive")
def market_massive(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    instrument: str = typer.Option(
        "acciones", "--instrument", help="Tipo de instrumento (default: acciones)"
    ),
    country: str = typer.Option("argentina", "--country", help="País (default: argentina)"),
):
    """Cotizaciones masivas por tipo de instrumento."""
    output_flags(json, csv, verbose, debug)
    country = resolve_country(country)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_massive_quotes", instrumento=instrument, pais=country)
    titulos = data.titulos if hasattr(data, "titulos") else data
    print(
        OutputFormatter.render(
            titulos, columns=MASSIVE_COLUMNS, color_columns=("variacion_porcentual",)
        )
    )


@market_app.command("panel")
def market_panel(
    panel: str = typer.Argument(..., help="Panel, ej: merval"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    instrument: str = typer.Option(
        "acciones", "--instrument", help="Tipo de instrumento (default: acciones)"
    ),
    country: str = typer.Option("argentina", "--country", help="País (default: argentina)"),
):
    """Cotizaciones de un panel (ej: merval)."""
    output_flags(json, csv, verbose, debug)
    country = resolve_country(country)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "get_panel_quotes", instrumento=instrument, panel=panel, pais=country
        )
    titulos = data.titulos if hasattr(data, "titulos") else data
    print(
        OutputFormatter.render(
            titulos, columns=MASSIVE_COLUMNS, color_columns=("variacion_porcentual",)
        )
    )


@market_app.command("detail")
def market_detail(
    symbol: str = typer.Argument(..., help="Símbolo, ej: GGAL"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    market: str = typer.Option("bCBA", "--market", help="Mercado (default: bCBA)"),
):
    """Cotización detallada (libro de ofertas)."""
    output_flags(json, csv, verbose, debug)
    market = resolve_market(market)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_stock_quote_detailed", simbolo=symbol, mercado=market)
    print(OutputFormatter.render(data, columns=DETAIL_COLUMNS, color_columns=("variacion",)))


@market_app.command("mep-rate")
def market_mep_rate(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    symbol: str = typer.Option(
        "AL30", "--symbol", help="Bono para calcular el MEP (default: AL30)"
    ),
):
    """Cotización del dólar MEP según un bono."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_mep_dollar_rate", symbol=symbol)
    if isinstance(data, dict):
        print(OutputFormatter.render(data))
    else:
        print(f"Dólar MEP ({symbol}): ${data}")
