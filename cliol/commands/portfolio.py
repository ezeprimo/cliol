"""Comandos de portafolio, cuenta, operaciones y perfil (solo consulta)."""

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.constants import COUNTRIES, OPERATION_STATES, normalize_choice
from cliol.errors import APIError, CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter

portfolio_app = typer.Typer(help="Portafolio y posiciones (solo consulta).", no_args_is_help=True)
account_app = typer.Typer(help="Estado de cuenta (solo consulta).", no_args_is_help=True)
operations_app = typer.Typer(help="Historial de operaciones (solo consulta).", no_args_is_help=True)

PORTFOLIO_COLUMNS = {
    "titulo": "Título",
    "descripcion": "Descripción",
    "cantidad": "Cantidad",
    "ultimo_precio": "Precio",
    "valorizado": "Total ARS",
    "variacion_diaria": "P&L diario %",
    "ganancia_porcentaje": "P&L total %",
}
OPERATIONS_COLUMNS = {
    "numero": "N°",
    "fecha": "Fecha",
    "tipo": "Tipo",
    "simbolo": "Símbolo",
    "cantidad": "Cantidad",
    "precio": "Precio",
    "monto": "Monto",
    "estado": "Estado",
}
ACCOUNT_COLUMNS = {
    "numero": "N°",
    "tipo": "Tipo",
    "moneda": "Moneda",
    "disponible": "Disponible",
    "comprometido": "Comprometido",
    "saldo": "Saldo",
    "titulos_valorizados": "Títulos",
    "total": "Total",
}
PROFILE_COLUMNS = {
    "nombre": "Nombre",
    "apellido": "Apellido",
    "numero_cuenta": "Cuenta",
    "email": "Email",
    "dni": "DNI",
    "cuit_cuil": "CUIT/CUIL",
    "perfil_inversor": "Perfil",
}
EMPTY_PORTFOLIO = "Portafolio vacío."
EMPTY_OPERATIONS = "No se encontraron operaciones."
OP_NOT_FOUND = "Operación {numero} no encontrada."


def resolve_country(value: str) -> str:
    canonical = normalize_choice(value, COUNTRIES)
    if canonical is None:
        raise CliolError(f"País inválido: {value}. Valores válidos: {', '.join(COUNTRIES)}")
    return canonical


def resolve_state(value: str) -> str:
    canonical = normalize_choice(value, OPERATION_STATES)
    if canonical is None:
        raise CliolError(f"Estado inválido: {value}. Valores válidos: {', '.join(OPERATION_STATES)}")
    return canonical


def _not_found(exc: Exception) -> bool:
    return "404" in str(exc)


@portfolio_app.command("show")
def portfolio_show(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    country: str = typer.Option("argentina", "--country", help="País (default: argentina)"),
):
    """Muestra las posiciones del portafolio con P&L coloreado."""
    output_flags(json, csv, verbose, debug)
    country = resolve_country(country)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_portfolio", pais=country)
    activos = data.activos if hasattr(data, "activos") else data
    if not activos:
        print(EMPTY_PORTFOLIO)
        return
    rows = [flat_position(item) for item in activos]
    print(
        OutputFormatter.render(
            rows,
            columns=PORTFOLIO_COLUMNS,
            color_columns=("variacion_diaria", "ganancia_porcentaje"),
        )
    )


def flat_position(item) -> dict:
    """Aplana una posición: extrae simbolo/descripcion de titulo anidado."""
    titulo = getattr(item, "titulo", None) or {}
    fields = {
        "titulo": titulo.simbolo if hasattr(titulo, "simbolo") else titulo.get("simbolo", ""),
        "descripcion": getattr(titulo, "descripcion", "") if hasattr(titulo, "descripcion") else "",
    }
    for name in (
        "cantidad",
        "comprometido",
        "puntos_variacion",
        "variacion_diaria",
        "ultimo_precio",
        "ppc",
        "ganancia_porcentaje",
        "ganancia_dinero",
        "valorizado",
    ):
        fields[name] = getattr(item, name, None)
    return fields


@account_app.command("status")
def account_status(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Muestra balances y estadísticas de la cuenta."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_account_status")
    cuentas = data.cuentas if hasattr(data, "cuentas") else []
    rows = [
        {
            "numero": c.numero,
            "tipo": c.tipo,
            "moneda": c.moneda,
            "disponible": c.disponible,
            "comprometido": c.comprometido,
            "saldo": c.saldo,
            "titulos_valorizados": c.titulos_valorizados,
            "total": c.total,
        }
        for c in cuentas
    ]
    print(OutputFormatter.render(rows, columns=ACCOUNT_COLUMNS))


@operations_app.command("list")
def operations_list(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    state: str = typer.Option(None, "--state", help="Estado (todas|pendientes|terminadas|canceladas)"),
    from_date: str = typer.Option(None, "--from", help="Fecha desde (YYYY-MM-DD)"),
    to_date: str = typer.Option(None, "--to", help="Fecha hasta (YYYY-MM-DD)"),
):
    """Lista operaciones con filtros opcionales."""
    output_flags(json, csv, verbose, debug)
    estado = resolve_state(state) if state else None
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "get_operations", estado=estado, fecha_desde=from_date, fecha_hasta=to_date
        )
    if not data:
        print(EMPTY_OPERATIONS)
        return
    rows = [
        {
            "numero": op.numero,
            "fecha": op.fecha_orden,
            "tipo": op.tipo,
            "simbolo": op.simbolo,
            "cantidad": op.cantidad,
            "precio": op.precio,
            "monto": op.monto,
            "estado": op.estado,
        }
        for op in data
    ]
    print(OutputFormatter.render(rows, columns=OPERATIONS_COLUMNS))


@operations_app.command("show")
def operations_show(
    numero: int = typer.Argument(..., help="Número de operación"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Detalle de una operación."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        try:
            data = client.dispatch("get_operation_detail", numero=numero)
        except APIError as exc:
            if _not_found(exc):
                raise CliolError(OP_NOT_FOUND.format(numero=numero)) from exc
            raise
    print(OutputFormatter.render(data))


def profile_command(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Muestra los datos del perfil IOL."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch("get_profile_data")
    row = {
        "nombre": data.nombre,
        "apellido": data.apellido,
        "numero_cuenta": data.numero_cuenta,
        "email": data.email,
        "dni": data.dni,
        "cuit_cuil": data.cuit_cuil,
        "perfil_inversor": data.perfil_inversor,
    }
    print(OutputFormatter.render(row, columns=PROFILE_COLUMNS))
