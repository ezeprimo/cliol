"""Gestión de configuración TOML de cliol.

Almacena credenciales IOL y el estado de la operatoria en un archivo TOML
ubicado en el directorio de configuración de la plataforma
(`platformdirs.user_config_dir("cliol")`). El directorio se crea con
permisos 0700 y el archivo con 0600.
"""

import os
from pathlib import Path
from typing import Optional

import platformdirs

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

from cliol.errors import ConfigError

__all__ = ["ConfigManager"]


def _loads(content: bytes) -> dict:
    try:
        return tomllib.loads(content.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Error de configuración: {exc}") from exc


class ConfigManager:
    """Carga, guarda y consulta la configuración TOML de cliol."""

    APP_NAME = "cliol"
    FILE_NAME = "config.toml"
    PASSWORD_KEYS = ("iol.password", "trading.password_hash")
    MASK = "********"

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is not None:
            self._path = Path(config_path)
        else:
            config_dir = platformdirs.user_config_dir(self.APP_NAME)
            self._path = Path(config_dir) / self.FILE_NAME

    @property
    def config_path(self) -> Path:
        return self._path

    @property
    def config_dir(self) -> Path:
        return self._path.parent

    def load(self) -> dict:
        """Carga la configuración; devuelve {} si el archivo no existe."""
        if not self._path.exists():
            return {}
        with open(self._path, "rb") as handle:
            return _loads(handle.read())

    def save(self, config: dict) -> None:
        """Escribe la configuración con directorio 0700 y archivo 0600."""
        self.config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        import tomli_w

        content = tomli_w.dumps(config)
        temporary = self._path.with_suffix(".tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(temporary, 0o600)
        os.replace(temporary, self._path)
        os.chmod(self._path, 0o600)

    def get(self, key: str) -> str:
        """Devuelve el valor de una clave con puntos (ej: 'iol.username')."""
        value = self._get_raw(key)
        if value is None:
            raise ConfigError(f"Clave de configuración no encontrada: {key}")
        return str(value)

    def _get_raw(self, key: str):
        node = self.load()
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def set(self, key: str, value: str) -> None:
        """Persiste una clave con puntos creando las secciones necesarias."""
        config = self.load()
        parts = key.split(".")
        node = config
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        self.save(config)

    def is_trading_enabled(self) -> bool:
        value = self.load().get("trading", {}).get("enabled", False)
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"

    def get_password_hash(self) -> Optional[str]:
        value = self._get_raw("trading.password_hash")
        return str(value) if value else None

    def redact(self, config: dict) -> dict:
        """Copia de la configuración con las claves de contraseña enmascaradas."""
        redacted = {}
        for key, value in config.items():
            if isinstance(value, dict):
                redacted[key] = self.redact(value)
            else:
                redacted[key] = value
        for key in self.PASSWORD_KEYS:
            parts = key.split(".")
            node = redacted
            for part in parts[:-1]:
                if not isinstance(node.get(part), dict):
                    break
                node = node[part]
            else:
                if parts[-1] in node:
                    node[parts[-1]] = self.MASK
        return redacted

    def dotted_pairs(self, config: dict) -> list:
        """Aplana la configuración anidada en pares (clave con puntos, valor)."""
        pairs = []

        def walk(node: dict, prefix: str = ""):
            for key, value in node.items():
                dotted = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    walk(value, dotted)
                else:
                    pairs.append((dotted, value))

        walk(config)
        return pairs
