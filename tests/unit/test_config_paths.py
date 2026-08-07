"""Unit tests for cross-platform config path resolution."""

import platform
from pathlib import Path

import pytest

from cliol.config import ConfigManager


def test_config_dir_is_under_user_config():
    """ConfigManager uses platformdirs.user_config_dir for default path."""
    import platformdirs

    cm = ConfigManager()
    expected_dir = platformdirs.user_config_dir("cliol")
    assert str(cm.config_dir) == expected_dir


def test_config_filename_is_config_toml():
    """Config file is named 'config.toml'."""
    cm = ConfigManager()
    assert cm.config_path.name == "config.toml"


def test_custom_path_overrides_default():
    """Explicit config_path overrides the platformdirs default."""
    custom = Path("/custom/path/myconfig.toml")
    cm = ConfigManager(config_path=custom)
    assert cm.config_path == custom
    assert cm.config_dir == custom.parent


def test_app_name_constant():
    """APP_NAME is 'cliol'."""
    assert ConfigManager.APP_NAME == "cliol"


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific permission test")
def test_linux_config_dir_permissions(tmp_path):
    """On Linux, config directory is created with 0o700 permissions."""
    import os

    cm = ConfigManager(config_path=tmp_path / "cliol" / "config.toml")
    cm.set("iol.username", "test")
    mode = os.stat(cm.config_dir).st_mode & 0o777
    assert mode == 0o700


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific permission test")
def test_linux_config_file_permissions(tmp_path):
    """On Linux, config file is created with 0o600 permissions."""
    import os

    cm = ConfigManager(config_path=tmp_path / "config.toml")
    cm.set("iol.username", "test")
    mode = os.stat(cm.config_path).st_mode & 0o777
    assert mode == 0o600
