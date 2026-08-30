"""Update checker: cache, fetch, semver, guards, banner."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import platformdirs
from rich.console import Console

CACHE_TTL = 86400
TRUNK_ALLOWLIST = {
    (),
    ("setup",),
    ("auth", "test"),
    ("market", "quote"),
    ("market", "data"),
    ("portfolio", "show"),
    ("account", "status"),
    ("operations", "list"),
    ("fci", "list"),
    ("config", "list"),
}


def get_cache_path() -> Path:
    """Return primary cache path; fallback if primary not writable/creatable."""
    primary = Path(platformdirs.user_cache_dir("cliol")) / "update_cache.json"
    fallback = Path.home() / ".config" / "cliol" / ".update_cache.json"
    # If primary dir exists and is not writable, use fallback; otherwise try primary.
    # We do not create dirs here; caller handles mkdir.
    # Simple heuristic: if primary parent == fallback parent, just return primary.
    # But if platformdirs returns something unexpected, fallback ensures we have a writable location.
    # For now, always return primary unless its parent is read-only or cannot be created.
    # Check if we can stat parent; if it exists and not writable, fallback.
    try:
        parent = primary.parent
        if parent.exists():
            # Check writability
            if not os.access(parent, os.W_OK):
                return fallback
        return primary
    except Exception:
        return fallback


def _read_cache(path: Path) -> dict | None:
    """Read cache file; corrupt/missing -> None."""
    try:
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return None
        if "latest_version" not in data or "checked_at" not in data:
            return None
        return data
    except Exception:
        return None


def _write_cache(path: Path, latest: str) -> None:
    """Atomic write with 0700 dir and 0600 file."""
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Ensure dir permissions 0700 even if existed
        try:
            os.chmod(path.parent, 0o700)
        except Exception:
            pass
        checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data = {"latest_version": latest, "checked_at": checked_at}
        tmp = path.with_suffix(".tmp")
        # Write to tmp
        tmp.write_text(json.dumps(data), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except Exception:
            pass
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
    except Exception:
        # Never raise for banner path
        pass


def is_newer(latest: str, current: str) -> bool:
    """Compare versions via packaging.Version, strip leading v, InvalidVersion -> False."""
    try:
        from packaging.version import InvalidVersion, Version
    except ImportError:
        return False
    try:
        # strip leading v / V
        latest_norm = latest.lstrip("vV").strip()
        current_norm = current.lstrip("vV").strip()
        return Version(latest_norm) > Version(current_norm)
    except InvalidVersion:
        return False
    except Exception:
        return False


def fetch_latest_version(timeout: float = 2.0) -> str | None:
    """Fetch latest release tag from GitHub, strip v, silent None on any failure."""
    url = "https://api.github.com/repos/ezeprimo/cliol/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "cliol-update-checker",
    }
    # Try httpx lazily
    try:
        import importlib.util

        if importlib.util.find_spec("httpx") is not None:
            import httpx

            try:
                resp = httpx.get(url, timeout=timeout, headers=headers)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                tag = data.get("tag_name") or data.get("name") or ""
                if not tag:
                    return None
                return str(tag).lstrip("vV").strip() or None
            except Exception:
                return None
    except Exception:
        pass

    # Fallback urllib
    try:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            if code != 200:
                return None
            body = resp.read()
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                return None
            tag = data.get("tag_name") or data.get("name") or ""
            if not tag:
                return None
            return str(tag).lstrip("vV").strip() or None
    except Exception:
        return None


def _is_update_check_enabled() -> bool:
    """Check config updates.check alias update_check.enabled; false/0/no -> disabled."""
    try:
        from cliol.config import ConfigManager

        return ConfigManager().is_update_check_enabled()
    except Exception:
        return True


def _parse_trunk(argv) -> tuple:
    """Parse argv into command tuple for trunk check, ignoring flags and args after."""
    if argv is None:
        argv = sys.argv
    # argv may include program name at [0]; skip it if it doesn't look like a flag and contains cliol or path
    args = list(argv)
    # Remove program name if present (first arg not starting with - and maybe contains cliol or path)
    # Heuristic: if first arg contains '/' or is 'cliol', treat as program name.
    if args and not args[0].startswith("-"):
        # Check if it's program name: could be 'cliol' or path ending with cliol
        first = args[0]
        if "cliol" in first or "/" in first or "\\" in first:
            args = args[1:]
        elif first == "python" or first.endswith("python"):
            # When invoked via python -m cliol, argv[0] is ..., but next is -m and cliol; handled below
            pass
    # Filter out flags and their values? Simplify: take first 2 non-flag args as command
    # Flags start with -
    cmd_parts = []
    for arg in args:
        if arg.startswith("-"):
            continue
        cmd_parts.append(arg)
        if len(cmd_parts) >= 2:
            break
    return tuple(cmd_parts)


def should_check(argv=None) -> bool:
    """Return True only if all guards pass and command is in trunk allowlist."""
    try:
        if argv is None:
            argv = sys.argv
        # Early help/version bypass
        for flag in ("--help", "-h", "--version"):
            if flag in argv:
                return False
        # TTY guard
        try:
            if not sys.stderr.isatty():
                return False
        except Exception:
            return False
        # CI guards
        if os.environ.get("CI"):
            return False
        if os.environ.get("GITHUB_ACTIONS"):
            return False
        if os.environ.get("TERM") == "dumb":
            return False
        # Format guards
        if "--json" in argv or "--csv" in argv:
            return False
        # Also check via get_format if set? Check output state
        try:
            from cliol.output import get_format

            fmt = get_format()
            if fmt in ("json", "csv"):
                return False
        except Exception:
            pass
        # Env opt-out
        env_val = os.environ.get("CLIOL_NO_UPDATE_CHECK", "")
        if env_val.strip().lower() in ("1", "true", "yes", "on"):
            return False
        # Config opt-out
        if not _is_update_check_enabled():
            return False
        # Trunk allowlist
        trunk = _parse_trunk(argv)
        # Handle -m invocation: if argv is ["-m", "cliol", ...] etc, _parse_trunk may include -m; already filtered flags
        # Also handle case where argv[0] is python
        # For safety, also filter empty
        # Normalize trunk: need to consider that "python -m cliol market quote" => argv = ["...python", "-m", "cliol", "market", "quote"]
        # Our logic removes program name but not -m; since -m starts with -, it's skipped, "cliol" next is taken as cmd_parts[0]? That would be wrong.
        # Let's also strip leading "cliol" if it appears as first cmd part due to -m invocation
        # If trunk starts with "cliol", shift
        if trunk and trunk[0] == "cliol":
            trunk = trunk[1:] if len(trunk) > 1 else ()
            # Need to re-parse after removing cliol
            # Actually if argv was [-m, cliol, market, quote], cmd_parts would be ["cliol", "market"] => trunk ("cliol","market") -> we want ("market","quote")
            # So if trunk[0]=="cliol" and len==2, take second element plus next arg
            # Let's handle more robustly: if "cliol" in trunk, remove it
            # Simpler: filter "cliol" from cmd_parts
            # For now, handle the specific case: if trunk == ("cliol","market") etc, we missed second part. Let's just remove cliol and re-evaluate
            # To avoid complexity, handle by filtering cliol from args
            pass
        # If cliol/python token leaked into trunk (python -m case), recompute without it
        if "cliol" in trunk or any("python" in p.lower() for p in trunk):
            raw_args = list(argv)
            all_parts = [a for a in raw_args if not a.startswith("-") and a != "cliol"]
            all_parts = [p for p in all_parts if "python" not in p.lower()]
            trunk = tuple(all_parts[:2])
        if trunk not in TRUNK_ALLOWLIST:
            return False
        return True
    except Exception:
        return False


def check_and_notify() -> None:
    """Guarded banner to stderr via Rich Console, never raise, 24h throttle."""
    try:
        if not should_check():
            return
        cache_path = get_cache_path()
        latest = None
        # Try cache first
        data = _read_cache(cache_path)
        use_cache = False
        if data is not None:
            try:
                checked_at_str = data.get("checked_at", "")
                # Parse ISO, handle Z
                checked_at = datetime.fromisoformat(checked_at_str.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - checked_at).total_seconds()
                if age < CACHE_TTL:
                    latest = data.get("latest_version")
                    use_cache = True
            except Exception:
                pass
        if not use_cache:
            fetched = fetch_latest_version(timeout=2.0)
            if fetched:
                latest = fetched
                # Write on success only
                try:
                    _write_cache(cache_path, latest)
                except Exception:
                    pass
            else:
                # Fetch failed, try to use stale cache if available (if fetch failed but cache exists, maybe use it?)
                # If fetch failed and no cache, nothing to do
                if data is not None:
                    latest = data.get("latest_version")
                else:
                    return
        if not latest:
            return
        # Compare
        from cliol import __version__ as current_version

        if not is_newer(latest, current_version):
            return
        # Print banner to stderr via Rich
        try:
            console = Console(file=sys.stderr, force_terminal=False)
            # Unified banner per design
            banner = (
                f"Update available: {current_version} -> {latest}\n"
                f"  curl -fsSL https://raw.githubusercontent.com/ezeprimo/cliol/main/install.sh | bash\n"
                f"  or: pip install -U cliol\n"
                f"  https://github.com/ezeprimo/cliol/releases"
            )
            console.print(banner)
        except Exception:
            # Fallback plain stderr
            try:
                print(
                    f"Update available: {current_version} -> {latest}",
                    file=sys.stderr,
                )
            except Exception:
                pass
    except Exception:
        # Never raise, preserve exit codes
        return
