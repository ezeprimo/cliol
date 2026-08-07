"""Unit tests for ConfigManager: TOML load/save, dotted keys, permissions, redaction."""

import os

import pytest

from cliol.config import ConfigManager
from cliol.errors import ConfigError


@pytest.fixture()
def config_manager(tmp_path):
    return ConfigManager(config_path=tmp_path / "config.toml")


def test_config_path_defaults_under_config_dir(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "sub" / "config.toml")
    assert cm.config_path == tmp_path / "sub" / "config.toml"
    assert cm.config_dir == tmp_path / "sub"


def test_load_missing_config_returns_empty_dict(config_manager):
    assert config_manager.load() == {}


def test_set_creates_dotted_sections_and_persists(config_manager):
    config_manager.set("iol.username", "mi_usuario")
    config_manager.set("trading.enabled", "true")
    data = config_manager.load()
    assert data["iol"]["username"] == "mi_usuario"
    assert data["trading"]["enabled"] == "true"


def test_set_saves_file_with_0600_permissions(config_manager):
    config_manager.set("iol.username", "mi_usuario")
    mode = os.stat(config_manager.config_path).st_mode & 0o777
    assert mode == 0o600


def test_save_creates_directory_with_0700_permissions(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "nest" / "deep" / "config.toml")
    cm.set("iol.username", "x")
    assert cm.config_dir.exists()
    mode = os.stat(cm.config_dir).st_mode & 0o777
    assert mode == 0o700


def test_get_existing_key(config_manager):
    config_manager.set("iol.username", "mi_usuario")
    assert config_manager.get("iol.username") == "mi_usuario"


def test_get_missing_key_raises_config_error(config_manager):
    with pytest.raises(ConfigError) as exc:
        config_manager.get("clave.invalida")
    assert "Clave de configuración no encontrada: clave.invalida" in str(exc.value)


def test_is_trading_enabled_false_by_default(config_manager):
    assert config_manager.is_trading_enabled() is False


def test_is_trading_enabled_true_when_set(config_manager):
    config_manager.set("trading.enabled", "true")
    assert config_manager.is_trading_enabled() is True


def test_password_hash_accessors(config_manager):
    config_manager.set("trading.password_hash", "$2b$12$abc")
    assert config_manager.get_password_hash() == "$2b$12$abc"
    assert config_manager.get_password_hash_or_none() == "$2b$12$abc"


def test_redact_masks_password_fields(config_manager):
    config_manager.set("iol.password", "secreto")
    config_manager.set("trading.password_hash", "$2b$12$hash")
    redacted = config_manager.redact(config_manager.load())
    assert redacted["iol"]["password"] == "********"
    assert redacted["trading"]["password_hash"] == "********"
    assert "secreto" not in repr(redacted)


def test_redact_keeps_plain_values(config_manager):
    config_manager.set("iol.username", "mi_usuario")
    redacted = config_manager.redact(config_manager.load())
    assert redacted["iol"]["username"] == "mi_usuario"


def test_dotted_pairs_flattens_nested_sections(config_manager):
    config_manager.set("iol.username", "u")
    config_manager.set("trading.enabled", "false")
    pairs = dict(config_manager.dotted_pairs(config_manager.load()))
    assert pairs == {"iol.username": "u", "trading.enabled": "false"}


def test_load_corrupt_toml_raises_config_error(config_manager, tmp_path):
    config_manager.config_path.write_text("no es toml {[", encoding="utf-8")
    with pytest.raises(ConfigError):
        config_manager.load()
