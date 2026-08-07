"""Errores de cliol con su código de salida correspondiente.

Mapa de códigos de salida (spec cli-app):
    1 — error general / API / configuración
    2 — error de red
    3 — credenciales inválidas
    4 — contraseña de gastos incorrecta
    5 — operatoria deshabilitada
"""


class CliolError(Exception):
    """Error base de cliol con código de salida."""

    exit_code = 1

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ConfigError(CliolError):
    """Error de configuración (archivo ausente, corrupto o clave inválida)."""

    exit_code = 1


class APIError(CliolError):
    """Error devuelto por la API de IOL."""

    exit_code = 1


class NetworkError(CliolError):
    """Fallo de conexión con la API de IOL."""

    exit_code = 2


class AuthError(CliolError):
    """Credenciales de IOL inválidas."""

    exit_code = 3


class WrongSpendingPassword(CliolError):
    """Contraseña de gastos incorrecta."""

    exit_code = 4


class TradingDisabled(CliolError):
    """Operatoria deshabilitada (modo consulta)."""

    exit_code = 5
