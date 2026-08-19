"""Regression tests for issue #8: --json gaps in mep-rate and operations list.

- market mep-rate --json must emit typed JSON (previously printed plain text).
- operations list must fall back to the executed (*_operada) fields so
  terminated operations show real values instead of nulls.
"""

import json
from dataclasses import dataclass

import pytest

from cliol.commands.market import market_mep_rate
from cliol.commands.portfolio import operations_list


@dataclass
class FakeOperacion:
    numero: int
    fecha_orden: str
    tipo: str
    simbolo: str
    estado: str
    cantidad: object
    cantidad_operada: object
    precio: object
    precio_operado: object
    monto: object
    monto_operado: object


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload

    def dispatch(self, method, **kwargs):
        return self._payload


class _FakeWrapper:
    payload = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return _FakeClient(self.payload)

    def __exit__(self, *args):
        return False


@pytest.fixture()
def fake_market_wrapper(monkeypatch):
    monkeypatch.setattr("cliol.commands.market.IOLClientWrapper", _FakeWrapper)


@pytest.fixture()
def fake_portfolio_wrapper(monkeypatch):
    monkeypatch.setattr("cliol.commands.portfolio.IOLClientWrapper", _FakeWrapper)


def _call(capsys, func, **flags):
    func(
        json=True,
        csv=False,
        verbose=False,
        debug=False,
        **flags,
    )
    return capsys.readouterr().out


def test_mep_rate_json_emits_typed_shape(capsys, fake_market_wrapper):
    _FakeWrapper.payload = 1515.24
    out = _call(capsys, market_mep_rate, symbol="AL30")
    assert json.loads(out) == {"simbolo": "AL30", "precio": 1515.24}


def test_mep_rate_json_with_custom_symbol(capsys, fake_market_wrapper):
    _FakeWrapper.payload = 1450.0
    out = _call(capsys, market_mep_rate, symbol="GD30")
    assert json.loads(out) == {"simbolo": "GD30", "precio": 1450.0}


def test_operations_list_falls_back_to_executed_fields(capsys, fake_portfolio_wrapper):
    _FakeWrapper.payload = [
        FakeOperacion(
            numero=1,
            fecha_orden="2026-08-18T10:00:00",
            tipo="Venta",
            simbolo="GGAL",
            estado="terminada",
            cantidad=None,
            cantidad_operada=5,
            precio=None,
            precio_operado=520.0,
            monto=None,
            monto_operado=2600.0,
        )
    ]
    out = _call(capsys, operations_list, state=None, from_date=None, to_date=None)
    data = json.loads(out)
    assert data[0]["cantidad"] == 5
    assert data[0]["precio"] == 520.0
    assert data[0]["monto"] == 2600.0


def test_operations_list_prefers_requested_fields(capsys, fake_portfolio_wrapper):
    _FakeWrapper.payload = [
        FakeOperacion(
            numero=2,
            fecha_orden="2026-08-18T10:00:00",
            tipo="Compra",
            simbolo="PAMP",
            estado="pendiente",
            cantidad=10,
            cantidad_operada=0,
            precio=3000.0,
            precio_operado=None,
            monto=30000.0,
            monto_operado=None,
        )
    ]
    out = _call(capsys, operations_list, state=None, from_date=None, to_date=None)
    data = json.loads(out)
    assert data[0]["cantidad"] == 10
    assert data[0]["precio"] == 3000.0
    assert data[0]["monto"] == 30000.0


def test_operations_list_keeps_legit_null_for_dividends(capsys, fake_portfolio_wrapper):
    _FakeWrapper.payload = [
        FakeOperacion(
            numero=3,
            fecha_orden="2026-08-18T10:00:00",
            tipo="Pago de Dividendos",
            simbolo="GGAL",
            estado="terminada",
            cantidad=None,
            cantidad_operada=None,
            precio=None,
            precio_operado=None,
            monto=None,
            monto_operado=None,
        )
    ]
    out = _call(capsys, operations_list, state=None, from_date=None, to_date=None)
    data = json.loads(out)
    assert data[0]["cantidad"] is None
    assert data[0]["precio"] is None
