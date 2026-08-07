"""Unit tests for OutputFormatter: json/csv/table rendering and flag handling."""

import csv
import io
import json
from dataclasses import dataclass

import pytest

from cliol.output import (
    OutputFormatter,
    color_for,
    get_format,
    set_debug,
    set_format,
    set_verbose,
)


@dataclass
class FakeModel:
    simbolo: str
    ultimo_precio: float
    variacion: float


@pytest.fixture(autouse=True)
def reset_format():
    set_format("table")
    set_verbose(False)
    set_debug(False)
    yield
    set_format("table")
    set_verbose(False)
    set_debug(False)


def test_default_format_is_table():
    assert get_format() == "table"


def test_set_format_json():
    set_format("json")
    assert get_format() == "json"


def test_json_output_is_valid_json_string():
    set_format("json")
    raw = {"simbolo": "GGAL", "ultimoPrecio": 1234.5}
    rendered = OutputFormatter.render(raw)
    assert json.loads(rendered) == raw


def test_json_handles_dataclasses_and_dates():
    set_format("json")
    from datetime import datetime

    rendered = OutputFormatter.json(FakeModel("GGAL", 100.0, 1.5))
    data = json.loads(rendered)
    assert data["simbolo"] == "GGAL"
    assert data["ultimo_precio"] == 100.0
    assert data["variacion"] == 1.5
    rendered_date = OutputFormatter.json({"fecha": datetime(2026, 1, 1, 12, 0, 0)})
    assert json.loads(rendered_date)["fecha"] == "2026-01-01T12:00:00"


def test_csv_output_with_header():
    set_format("csv")
    data = [FakeModel("GGAL", 100.0, 1.0), FakeModel("PAMP", 2000.0, -2.5)]
    columns = {"simbolo": "Símbolo", "ultimo_precio": "Precio", "variacion": "Variación"}
    raw = OutputFormatter.render(data, columns=columns)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert reader.fieldnames == ["Símbolo", "Precio", "Variación"]
    assert len(rows) == 2
    assert rows[0]["Símbolo"] == "GGAL"
    assert rows[1]["Variación"] == "-2.5"


def test_table_output_contains_headers_and_cells():
    set_format("table")
    data = FakeModel("GGAL", 100.0, 1.0)
    columns = {"simbolo": "Símbolo", "ultimo_precio": "Precio"}
    out = OutputFormatter.render(data, columns=columns)
    assert "Símbolo" in out
    assert "GGAL" in out
    assert "100.0" in out


def test_color_for_positive_green_negative_red():
    assert color_for("variacion", 1.5) == "green"
    assert color_for("variacion", -1.5) == "red"
    assert color_for("variacion", 0.0) is None
    assert color_for("variacion", None) is None
    assert color_for("simbolo", "GGAL") is None


def test_render_empty_list_produces_header_only_table():
    set_format("table")
    out = OutputFormatter.render([], columns={"a": "A"})
    assert "A" in out


def test_to_rows_raises_on_unsupported_input():
    with pytest.raises(TypeError):
        OutputFormatter.to_rows(42)
