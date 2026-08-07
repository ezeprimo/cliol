"""Unit tests for TradingGate: enable check and spending-password prompt."""

import pytest

from cliol.config import ConfigManager
from cliol.errors import TradingDisabled, WrongSpendingPassword
from cliol.security import SpendingPassword
from cliol.trading_gate import TradingGate


def _gate(tmp_path, enabled: bool, password=None) -> TradingGate:
    cm = ConfigManager(config_path=tmp_path / "config.toml")
    if password:
        cm.set("trading.password_hash", SpendingPassword.create(password))
        cm.set("trading.enabled", "true" if enabled else "false")
    else:
        cm.set("trading.enabled", "true" if enabled else "false")
    return TradingGate(cm)


def test_check_passes_when_enabled(tmp_path):
    gate = _gate(tmp_path, enabled=True, password="clave1")
    assert gate.check() is None


def test_check_raises_trading_disabled_when_disabled(tmp_path):
    gate = _gate(tmp_path, enabled=False, password="clave1")
    with pytest.raises(TradingDisabled) as exc:
        gate.check()
    assert "Operatoria deshabilitada. Para operar, ejecute: cliol config trading enable" in str(exc.value)


def test_prompt_password_accepts_correct(tmp_path, monkeypatch):
    gate = _gate(tmp_path, enabled=True, password="clave1")
    monkeypatch.setattr(gate, "_ask_password", lambda: "clave1")
    assert gate.prompt_password() is True


def test_prompt_password_rejects_wrong(tmp_path, monkeypatch):
    gate = _gate(tmp_path, enabled=True, password="clave1")
    monkeypatch.setattr(gate, "_ask_password", lambda: "mal")
    with pytest.raises(WrongSpendingPassword) as exc:
        gate.prompt_password()
    assert str(exc.value) == "Contraseña de gastos incorrecta."


def test_prompt_password_uses_masked_rich_prompt(tmp_path, monkeypatch):
    gate = _gate(tmp_path, enabled=True, password="clave1")
    import rich.prompt

    called = {}

    def fake_ask(text, password=False):
        called["password"] = password
        return "clave1"

    monkeypatch.setattr(rich.prompt.Prompt, "ask", staticmethod(fake_ask))
    assert gate.prompt_password() is True
    assert called.get("password") is True
