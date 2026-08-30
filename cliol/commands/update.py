"""Command `cliol update check` — explicit version check."""

import json
import sys

import typer
from rich.console import Console

from cliol import __version__
from cliol.update_checker import (
    CACHE_TTL,
    _read_cache,
    _write_cache,
    fetch_latest_version,
    get_cache_path,
    is_newer,
)

update_app = typer.Typer(help="Actualizaciones de cliol.", no_args_is_help=True)


def _get_cached_latest():
    """Return cached latest if fresh, else None."""
    try:
        path = get_cache_path()
        data = _read_cache(path)
        if data is None:
            return None
        # Check age
        from datetime import datetime, timezone

        checked_at_str = data.get("checked_at", "")
        checked_at = datetime.fromisoformat(checked_at_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - checked_at).total_seconds()
        if age < CACHE_TTL:
            return data.get("latest_version")
        return None
    except Exception:
        return None


@update_app.command("check")
def update_check(
    json_output: bool = typer.Option(False, "--json", is_flag=True, help="Salida como JSON."),
    force: bool = typer.Option(
        False, "--force", is_flag=True, help="Forzar consulta a GitHub, ignorar caché."
    ),
):
    """Verifica si hay una versión más nueva disponible."""
    current = __version__
    latest = None

    # Try cache unless force
    if not force:
        latest = _get_cached_latest()

    if latest is None:
        # Need to fetch
        latest = fetch_latest_version(timeout=2.0)
        if latest is None:
            # Fetch failed
            print("Error: No se pudo obtener la última versión.", file=sys.stderr)
            raise typer.Exit(code=2)
        # Write cache on success
        try:
            _write_cache(get_cache_path(), latest)
        except Exception:
            pass

    update_available = is_newer(latest, current)

    if json_output:
        data = {
            "current": current,
            "latest": latest,
            "update_available": update_available,
        }
        # Use json output to stdout, no banner
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        # Table/default output
        if update_available:
            console = Console()
            console.print(f"Update available: {current} -> {latest}")
            console.print(
                "  curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash"
            )
            console.print("  or: pip install -U cliol")
            console.print("  https://github.com/ezeprimo/cliol/releases")
        else:
            console = Console()
            console.print(f"cliol está actualizado ({current}).")
            if latest != current:
                console.print(f"Última versión: {latest}")

    raise typer.Exit(code=0)
