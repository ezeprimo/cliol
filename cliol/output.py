"""Formateo de salida: tabla (Rich), JSON y CSV.

El formato activo se guarda en el estado global del módulo (`get_format()`),
que los comandos setean con `set_format()` desde las banderas globales
`--json`/`--csv`.

El parámetro `columns` puede ser:
- un dict: `{"simbolo": "Símbolo", "ultimo_precio": "Precio"}` — keys = campos internos, values = nombres display
- una lista: `["simbolo", "ultimo_precio"]` — solo campos internos, sin rename
- None: todos los campos
"""

import csv
import io
import json
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text

__all__ = [
    "OutputFormatter",
    "color_for",
    "set_format",
    "get_format",
    "set_verbose",
    "get_verbose",
    "set_debug",
    "get_debug",
]

_STATE = {"format": "table", "verbose": False, "debug": False}


def set_format(fmt: str) -> None:
    _STATE["format"] = fmt


def get_format() -> str:
    return _STATE["format"]


def set_verbose(value: bool) -> None:
    _STATE["verbose"] = value


def get_verbose() -> bool:
    return _STATE["verbose"]


def set_debug(value: bool) -> None:
    _STATE["debug"] = value


def get_debug() -> bool:
    return _STATE["debug"]


def color_for(column: str, value) -> Optional[str]:
    """Estilo de color para un valor: verde si > 0, rojo si < 0."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num > 0:
        return "green"
    if num < 0:
        return "red"
    return None


def _value_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _normalize_columns(columns) -> tuple:
    """Devuelve (field_names, display_names) a partir del parámetro columns.

    - dict: field_names = keys, display_names = values
    - list: field_names = list, display_names = same
    - None: (None, None)
    """
    if columns is None:
        return None, None
    if isinstance(columns, dict):
        return list(columns.keys()), columns
    return list(columns), {k: k for k in columns}


class OutputFormatter:
    """Selecciona el formato de salida según el estado global."""

    @staticmethod
    def _dataclass_to_dict(item) -> dict:
        """Convierte un dataclass a dict usando nombres de campo."""
        if is_dataclass(item) and not isinstance(item, type):
            return {f.name: getattr(item, f.name) for f in fields(item)}
        if isinstance(item, dict):
            return dict(item)
        raise TypeError(f"Tipo de dato no soportado para salida: {type(item).__name__}")

    @staticmethod
    def to_rows(data, columns=None):
        """Normaliza dict/dataclass/lista a lista de dicts planos.

        Cuando `columns` está presente, devuelve solo esos campos en ese orden.
        """
        items = data if isinstance(data, list) else [data]
        field_names, _display_names = _normalize_columns(columns)
        rows = [OutputFormatter._dataclass_to_dict(item) for item in items]
        if field_names and rows:
            rows = [{key: row.get(key, "") for key in field_names} for row in rows]
        return rows

    @staticmethod
    def json(data) -> str:
        """JSON indentado; dataclasses y objetos se serializan con default=str."""

        def _serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        if is_dataclass(data) and not isinstance(data, type):
            data = asdict(data)
        elif isinstance(data, list):
            data = [
                asdict(item) if is_dataclass(item) and not isinstance(item, type) else item
                for item in data
            ]
        return json.dumps(data, ensure_ascii=False, indent=2, default=_serializer)

    @staticmethod
    def csv(data, columns=None) -> str:
        rows, fieldnames = OutputFormatter._prepare_tabular(data, columns)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

    @staticmethod
    def _prepare_tabular(data, columns=None) -> tuple:
        """Prepara rows y fieldnames (display names) para CSV/table."""
        field_names, display_names = _normalize_columns(columns)
        rows = OutputFormatter.to_rows(data, columns)
        if field_names is None and rows:
            field_names = list(rows[0].keys())
        if field_names is None:
            field_names = []
        if display_names is None:
            display_names = {k: k for k in field_names}

        out_fieldnames = [display_names.get(k, k) for k in field_names]

        # Rename row keys from internal names to display names
        out_rows = []
        for row in rows:
            out_rows.append({display_names.get(k, k): v for k, v in row.items()})
        return out_rows, out_fieldnames

    @staticmethod
    def table(data, columns=None, color_columns=()) -> str:
        """Tabla Rich con cabeceras; columnas de color pintan verde/rojo por signo."""
        rows, fieldnames = OutputFormatter._prepare_tabular(data, columns)
        table = Table(show_header=True, header_style="bold")
        for header in fieldnames:
            table.add_column(header, overflow="fold")
        for row in rows:
            styled_cells = []
            for key in fieldnames:
                value = row.get(key)
                text = Text(_value_to_str(value))
                style = color_for(key, value) if key in color_columns else None
                if style:
                    text.stylize(style)
                styled_cells.append(text)
            table.add_row(*styled_cells)
        console = Console(record=True, width=160, force_terminal=False)
        console.print(table)
        return console.export_text()

    @staticmethod
    def render(data, columns=None, color_columns=()) -> str:
        """Despacha según el formato global (table | json | csv)."""
        fmt = get_format()
        if fmt == "json":
            return OutputFormatter.json(data)
        if fmt == "csv":
            return OutputFormatter.csv(data, columns)
        return OutputFormatter.table(data, columns, color_columns)
