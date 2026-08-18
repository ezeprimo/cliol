"""Regression tests for issue #5: --json output must mirror the table data.

dispatch() always returns typed models now (single shape for all formats);
portfolio/account JSON must contain real values, not null/empty fields.
"""

import json
from dataclasses import dataclass

import pytest

from cliol.commands.portfolio import account_status, portfolio_show


@dataclass
class FakeTitulo:
    simbolo: str
    descripcion: str


@dataclass
class FakePosicion:
    cantidad: int
    comprometido: float
    puntos_variacion: float
    variacion_diaria: float
    ultimo_precio: float
    ppc: float
    ganancia_porcentaje: float
    ganancia_dinero: float
    valorizado: float
    titulo: FakeTitulo


@dataclass
class FakePortafolio:
    pais: str
    activos: list
    total_en_pesos: float


@dataclass
class FakeCuenta:
    numero: str
    tipo: str
    moneda: str
    disponible: float
    comprometido: float
    saldo: float
    titulos_valorizados: float
    total: float


@dataclass
class FakeEstadoCuenta:
    cuentas: list
    total_en_pesos: float
    estadisticas: dict


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
def fake_wrapper(monkeypatch):
    monkeypatch.setattr("cliol.commands.portfolio.IOLClientWrapper", _FakeWrapper)


def _position(simbolo="GGAL", cantidad=10):
    return FakePosicion(
        cantidad=cantidad,
        comprometido=0.0,
        puntos_variacion=1.5,
        variacion_diaria=2.3,
        ultimo_precio=1234.5,
        ppc=1100.0,
        ganancia_porcentaje=12.2,
        ganancia_dinero=1345.0,
        valorizado=12345.0,
        titulo=FakeTitulo(simbolo=simbolo, descripcion="Grupo Financiero Galicia"),
    )


def _call(capsys, func, **flags):
    func(
        json=True,
        csv=False,
        verbose=False,
        debug=False,
        **flags,
    )
    return capsys.readouterr().out


def test_portfolio_show_json_mirrors_table_data(capsys, fake_wrapper):
    _FakeWrapper.payload = FakePortafolio(
        pais="argentina", activos=[_position("GGAL", 10), _position("PAMP", 5)], total_en_pesos=999
    )
    out = _call(capsys, portfolio_show, country="argentina")
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["titulo"] == "GGAL"
    assert data[0]["descripcion"] == "Grupo Financiero Galicia"
    assert data[0]["cantidad"] == 10
    assert data[0]["ultimo_precio"] == 1234.5
    assert data[0]["ganancia_porcentaje"] == 12.2


def test_account_status_json_mirrors_table_data(capsys, fake_wrapper):
    _FakeWrapper.payload = FakeEstadoCuenta(
        cuentas=[FakeCuenta("123", "titulos", "ARS", 1000.0, 0.0, 1000.0, 5000.0, 6000.0)],
        total_en_pesos=6000.0,
        estadisticas={},
    )
    out = _call(capsys, account_status)
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["numero"] == "123"
    assert data[0]["moneda"] == "ARS"
    assert data[0]["disponible"] == 1000.0
    assert data[0]["total"] == 6000.0
