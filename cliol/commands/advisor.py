"""Comandos del Asesor de Inversiones: movimientos, test de perfil y venta asistida."""

import json

import typer

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.errors import CliolError
from cliol.options import CSV_OPTION, DEBUG_OPTION, JSON_OPTION, VERBOSE_OPTION, output_flags
from cliol.output import OutputFormatter
from cliol.prompts import ask_int
from cliol.trading_gate import TradingGate

advisor_app = typer.Typer(
    help="Asesor de inversiones: perfil, movimientos y ventas.", no_args_is_help=True
)

MOVEMENTS_COLUMNS = {
    "fecha": "Fecha",
    "movimiento": "Movimiento",
    "operacion": "Operación",
    "simbolo": "Símbolo",
    "cantidad": "Cantidad",
    "precio": "Precio",
    "importe": "Importe",
    "estado": "Estado",
}
PROFILE_COLUMNS = {
    "descripcion": "Perfil",
    "puntaje": "Puntaje",
    "puntaje_maximo": "Máximo",
    "es_conservador": "Conservador",
    "es_moderado": "Moderado",
    "es_agresivo": "Agresivo",
    "guardado": "Guardado",
}
SELL_RESULT_COLUMNS = {
    "numero_operacion": "Operación",
    "id_cliente": "Cliente",
    "simbolo": "Símbolo",
    "cantidad": "Cantidad",
    "precio": "Precio",
    "exito": "Éxito",
    "mensaje": "Mensaje",
}
PROFILE_DONE = "Perfil '{perfil}' guardado para el cliente '{cliente}'."
PROFILE_NOT_SAVED = "Perfil calculado pero no guardado (solo evaluación)."
PROFILE_SAVE_HINT = "Use 'cliol advisor save-profile' para persistir el perfil."


def _parse_answers(raw: str) -> list:
    """Convierte una cadena JSON de respuestas en la estructura de la API."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliolError("El JSON de --answers no es válido.") from exc
    if not isinstance(data, list):
        raise CliolError(
            "--answers debe ser una lista de objetos {'idPregunta':..., 'idRespuesta':...}."
        )
    clean = []
    for item in data:
        if not isinstance(item, dict) or "idPregunta" not in item or "idRespuesta" not in item:
            raise CliolError("Cada respuesta debe tener las claves 'idPregunta' e 'idRespuesta'.")
        clean.append({"idPregunta": item["idPregunta"], "idRespuesta": item["idRespuesta"]})
    return clean


def _ask_test(test) -> list:
    """Interactivo: recorre preguntas y devuelve respuestas [{idPregunta, idRespuesta}]."""
    respuestas = []
    for pregunta in getattr(test, "preguntas", []):
        print(f"Pregunta {pregunta.numero}: {pregunta.texto}")
        opciones = pregunta.opciones or []
        for opcion in opciones:
            print(f"  [{opcion.id}] {opcion.texto}")
        if not opciones:
            raise CliolError(f"La pregunta {pregunta.numero} no tiene opciones.")
        seleccion = None
        while seleccion is None:
            valor = ask_int("Seleccione una opción")
            if any(opcion.id == valor for opcion in opciones):
                seleccion = valor
            else:
                print(f"Opción inválida: {valor}")
        respuestas.append({"idPregunta": pregunta.id, "idRespuesta": seleccion})
    return respuestas


def _print_profile(profile) -> None:
    """Renderiza un PerfilInversor con sus estados derivados."""
    row = {
        "descripcion": getattr(profile, "descripcion", None),
        "puntaje": getattr(profile, "puntaje", None),
        "puntaje_maximo": getattr(profile, "puntaje_maximo", None),
        "es_conservador": getattr(profile, "es_conservador", False),
        "es_moderado": getattr(profile, "es_moderado", False),
        "es_agresivo": getattr(profile, "es_agresivo", False),
        "guardado": getattr(profile, "guardado", None),
    }
    print(OutputFormatter.render([row], columns=PROFILE_COLUMNS))


@advisor_app.command("movements")
def advisor_movements(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    since: str = typer.Option(None, "--since", help="Fecha desde (YYYY-MM-DD)"),
    until: str = typer.Option(None, "--until", help="Fecha hasta (YYYY-MM-DD)"),
    client_id: str = typer.Option(None, "--client-id", help="ID de cliente"),
    page: int = typer.Option(1, "--page", help="Página (default: 1)"),
    per_page: int = typer.Option(50, "--per-page", help="Registros por página (default: 50)"),
):
    """Consulta los movimientos del asesor."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        data = client.dispatch(
            "get_advisor_movements",
            fecha_desde=since,
            fecha_hasta=until,
            id_cliente=client_id,
            pagina=page,
            registros_por_pagina=per_page,
        )
    print(OutputFormatter.render(data, columns=MOVEMENTS_COLUMNS))


@advisor_app.command("test-questions")
def advisor_test_questions(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Muestra el título y descripción del test de perfil (solo lectura)."""
    output_flags(json, csv, verbose, debug)
    with IOLClientWrapper(ConfigManager(), verbose=verbose, debug=debug) as client:
        test = client.dispatch("get_investor_test_questions")
    for pregunta in getattr(test, "preguntas", []):
        print(f"Pregunta {pregunta.numero}: {pregunta.texto}")
        for opcion in pregunta.opciones or []:
            print(f"  [{opcion.id}] {opcion.texto}")


@advisor_app.command("calculate-profile")
def advisor_calculate_profile(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    answers: str = typer.Option(
        None,
        "--answers",
        help='Respuestas JSON: \'[{"idPregunta":1,"idRespuesta":2}]\' (si se omite, test interactivo)',
    ),
):
    """Calcula el perfil de inversor a partir del test (no lo guarda)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    if answers:
        respuestas = _parse_answers(answers)
        with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
            profile = client.dispatch("calculate_investor_profile", respuestas=respuestas)
    else:
        with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
            test = client.dispatch("get_investor_test_questions")
        respuestas = _ask_test(test)
        with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
            profile = client.dispatch("calculate_investor_profile", respuestas=respuestas)
    _print_profile(profile)
    print(PROFILE_NOT_SAVED)
    print(PROFILE_SAVE_HINT)


@advisor_app.command("save-profile")
def advisor_save_profile(
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
    client_id: str = typer.Option(..., "--client-id", help="ID de cliente"),
    answers: str = typer.Option(None, "--answers", help="Respuestas JSON"),
):
    """Guarda el perfil del inversor (solo lectura — no requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    if answers:
        respuestas = _parse_answers(answers)
    else:
        with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
            test = client.dispatch("get_investor_test_questions")
        respuestas = _ask_test(test)
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        profile = client.dispatch(
            "save_investor_profile", id_cliente=client_id, respuestas=respuestas
        )
    _print_profile(profile)
    print(PROFILE_DONE.format(perfil=getattr(profile, "descripcion", "?"), cliente=client_id))


@advisor_app.command("sell-usd")
def advisor_sell_usd(
    client_id: str = typer.Option(..., "--client-id", help="ID de cliente"),
    symbol: str = typer.Argument(..., help="Bono dólar a vender, ej: GD30"),
    quantity: int = typer.Argument(..., min=1, help="Cantidad"),
    price: float = typer.Argument(..., min=0, help="Precio en dólares"),
    json: bool = JSON_OPTION,
    csv: bool = CSV_OPTION,
    verbose: bool = VERBOSE_OPTION,
    debug: bool = DEBUG_OPTION,
):
    """Vende un bono en dólares como asesor (requiere operatoria)."""
    output_flags(json, csv, verbose, debug)
    config = ConfigManager()
    gate = TradingGate(config)
    gate.check()
    gate.prompt_password()
    with IOLClientWrapper(config, verbose=verbose, debug=debug) as client:
        result = client.dispatch(
            "advisor_sell_dollar_bond",
            id_cliente=client_id,
            simbolo=symbol,
            cantidad=quantity,
            precio=price,
        )
    print(OutputFormatter.render(result, columns=SELL_RESULT_COLUMNS))
