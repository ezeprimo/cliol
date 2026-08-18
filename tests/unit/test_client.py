"""Unit tests for IOLClientWrapper: lazy init, dispatch, errors, context manager."""

import pytest

from cliol.client import IOLClientWrapper
from cliol.config import ConfigManager
from cliol.errors import APIError, AuthError, CliolError, NetworkError
from cliol.output import set_format


class FakeIOLClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.closed = False

    def close(self):
        self.closed = True

    def get_stock_quote(self, symbol, market="bCBA", settlement_term="t1"):
        return {"tipado": symbol, "market": market, "term": settlement_term}

    def get_stock_quote_raw(self, symbol, market="bCBA", settlement_term="t1"):
        return {"raw": symbol, "market": market, "term": settlement_term}


@pytest.fixture()
def fake_iol(monkeypatch):
    """Replace cliol.client.IOLClient with FakeIOLClient and return the class."""
    monkeypatch.setattr("cliol.client.IOLClient", FakeIOLClient)
    return FakeIOLClient


@pytest.fixture()
def config_manager(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "config.toml")
    cm.set("iol.username", "u")
    cm.set("iol.password", "p")
    return cm


def test_client_is_lazy(config_manager, fake_iol):
    wrapper = IOLClientWrapper(config_manager)
    assert wrapper._client is None
    wrapper.dispatch("get_stock_quote", symbol="GGAL")
    assert isinstance(wrapper._client, FakeIOLClient)


def test_dispatch_uses_typed_method_by_default(config_manager, fake_iol):
    set_format("table")
    try:
        wrapper = IOLClientWrapper(config_manager)
        result = wrapper.dispatch("get_stock_quote", symbol="GGAL")
        assert result == {"tipado": "GGAL", "market": "bCBA", "term": "t1"}
    finally:
        set_format("table")


def test_dispatch_uses_typed_method_even_when_json(config_manager, fake_iol):
    """La salida JSON usa el mismo shape tipado que la tabla (issue #5)."""
    set_format("json")
    try:
        wrapper = IOLClientWrapper(config_manager)
        result = wrapper.dispatch("get_stock_quote", symbol="GGAL")
        assert result == {"tipado": "GGAL", "market": "bCBA", "term": "t1"}
    finally:
        set_format("table")


def test_dispatch_passes_kwargs_through(config_manager, fake_iol):
    set_format("table")
    try:
        wrapper = IOLClientWrapper(config_manager)
        result = wrapper.dispatch(
            "get_stock_quote", symbol="PAMP", market="nYSE", settlement_term="t2"
        )
        assert result["market"] == "nYSE"
        assert result["term"] == "t2"
    finally:
        set_format("table")


def test_context_manager_closes_client(config_manager, fake_iol):
    with IOLClientWrapper(config_manager) as wrapper:
        wrapper.dispatch("get_stock_quote", symbol="GGAL")
    assert wrapper._client.closed is True


def test_unknown_method_raises_cliol_error(config_manager, fake_iol):
    wrapper = IOLClientWrapper(config_manager)
    with pytest.raises(CliolError):
        wrapper.dispatch("no_such_method")


def _raise(exc):
    def _boom(*args, **kwargs):
        raise exc

    return _boom


def test_api_error_mapped(config_manager, fake_iol, monkeypatch):
    from pyIol import IOLAPIError

    wrapper = IOLClientWrapper(config_manager)
    wrapper._client = FakeIOLClient("u", "p")
    monkeypatch.setattr(
        FakeIOLClient, "get_stock_quote", _raise(IOLAPIError("Error en petición a /x: 500"))
    )
    with pytest.raises(APIError):
        wrapper.dispatch("get_stock_quote", symbol="GGAL")


def test_token_error_mapped_to_auth_error(config_manager, fake_iol, monkeypatch):
    from pyIol import IOLAPIError

    wrapper = IOLClientWrapper(config_manager)
    wrapper._client = FakeIOLClient("u", "p")
    monkeypatch.setattr(
        FakeIOLClient,
        "get_stock_quote",
        _raise(IOLAPIError("Error al obtener token: 401 Unauthorized")),
    )
    with pytest.raises(AuthError):
        wrapper.dispatch("get_stock_quote", symbol="GGAL")


def test_connection_error_mapped_to_network_error(config_manager, fake_iol, monkeypatch):
    from pyIol import IOLAPIError

    wrapper = IOLClientWrapper(config_manager)
    wrapper._client = FakeIOLClient("u", "p")
    monkeypatch.setattr(
        FakeIOLClient,
        "get_stock_quote",
        _raise(IOLAPIError("Error en petición a /x: ConnectError: conexión rechazada")),
    )
    with pytest.raises(NetworkError):
        wrapper.dispatch("get_stock_quote", symbol="GGAL")


def test_network_error_message(config_manager, fake_iol, monkeypatch):
    from pyIol import IOLAPIError

    wrapper = IOLClientWrapper(config_manager)
    wrapper._client = FakeIOLClient("u", "p")
    monkeypatch.setattr(
        FakeIOLClient,
        "get_stock_quote",
        _raise(IOLAPIError("Error en petición a /x: ConnectTimeout")),
    )
    with pytest.raises(NetworkError) as exc:
        wrapper.dispatch("get_stock_quote", symbol="GGAL")
    assert "No se pudo conectar con IOL. Verifique su conexión a internet." in str(exc.value)


def test_credentials_missing_raises_config_error(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "config.toml")
    wrapper = IOLClientWrapper(cm)
    with pytest.raises(CliolError) as exc:
        wrapper.dispatch("get_stock_quote", symbol="GGAL")
    assert "Credenciales no configuradas. Ejecute 'cliol setup' primero." in str(exc.value)
