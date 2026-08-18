"""Envoltorio del cliente IOL para cliol.

Gestiona la sesión de `pyIol.IOLClient` de forma perezosa (una por invocación),
traduce errores de py_iol a la jerarquía CliolError y despacha siempre a los
métodos tipados: tabla, CSV y JSON se serializan desde el mismo modelo, de
modo que la salida JSON refleja la tabla por construcción.
"""

try:  # httpx es dependencia de py_iol; puede no estar importable en algunos entornos
    import httpx
except ModuleNotFoundError:  # pragma: no cover
    httpx = None

from pyIol import IOLAPIError, IOLClient

from cliol.config import ConfigManager
from cliol.errors import APIError, AuthError, CliolError, NetworkError
from cliol.output import get_debug, get_verbose

__all__ = ["IOLClientWrapper"]

NETWORK_MARKERS = (
    "connect",
    "timeout",
    "connection",
    "timed out",
    "temporary failure",
    "name resolution",
    "max retries",
)
AUTH_MARKER = "Error al obtener token"
NETWORK_MESSAGE = "No se pudo conectar con IOL. Verifique su conexión a internet."
AUTH_MESSAGE = "Credenciales inválidas. Ejecute 'cliol auth test' para verificarlas."


def classify_error(exc: Exception) -> CliolError:
    """Traduce un error de py_iol a la jerarquía CliolError por su mensaje."""
    message = str(exc)
    lowered = message.lower()
    if AUTH_MARKER in message:
        return AuthError(AUTH_MESSAGE)
    if any(marker in lowered for marker in NETWORK_MARKERS):
        return NetworkError(NETWORK_MESSAGE)
    return APIError(message)


class IOLClientWrapper:
    """Maneja la sesión IOL y el despacho raw/tipado según el formato de salida."""

    def __init__(
        self,
        config: ConfigManager,
        verbose: bool = None,
        debug: bool = None,
    ):
        self.config = config
        self._client = None
        self._verbose = get_verbose() if verbose is None else verbose
        self._debug = get_debug() if debug is None else debug

    @property
    def client(self):
        if self._client is None:
            self._client = self._get_client()
        return self._client

    def get_credentials(self):
        config = self.config.load()
        iol = config.get("iol") or {}
        username = iol.get("username")
        password = iol.get("password")
        if not username or not password:
            raise CliolError("Credenciales no configuradas. Ejecute 'cliol setup' primero.")
        return username, password

    def _get_client(self):
        username, password = self.get_credentials()
        if self._verbose:
            self._log(
                f"Autenticando contra IOL con usuario {username!r} (token en memoria, 14.5 min)…"
            )
        if self._debug:
            self._log(self.config.redact(self.config.load()))
        return IOLClient(username, password)

    def _log(self, message: str) -> None:
        import sys

        print(f"[cliol] {message}", file=sys.stderr)

    def auth_test(self) -> bool:
        """Verifica las credenciales IOL contra la API (no hace peticiones de datos)."""
        return self.client.test_authentication()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def __enter__(self) -> "IOLClientWrapper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def dispatch(self, method: str, **kwargs):
        """Llama al método tipado de py_iol (shape único para todos los formatos)."""

        fn = getattr(self.client, method, None)
        if fn is None:
            raise CliolError(f"El método {method} no está disponible en el cliente IOL.")
        if self._verbose:
            self._log(f"Llamando a {method}({', '.join(f'{k}={v!r}' for k, v in kwargs.items())})")
        try:
            return fn(**kwargs)
        except IOLAPIError as exc:
            raise classify_error(exc) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - py_iol ya envuelve httpx
            raise NetworkError(NETWORK_MESSAGE) from exc
        except Exception as exc:
            if isinstance(exc, CliolError):
                raise
            raise CliolError(str(exc)) from exc
