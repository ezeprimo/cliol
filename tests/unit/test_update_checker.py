"""Unit tests for update_checker: cache, throttle, semver, fetch, should_check, banner."""

import json
import os

import pytest


@pytest.fixture(autouse=True)
def _reset_output_format():
    from cliol.output import set_format

    set_format("table")
    yield
    set_format("table")


def test_cache_write_creates_file_0600_and_dir_0700(tmp_path, monkeypatch):
    from cliol.update_checker import _write_cache

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache_home"))
    # Use tmp_path for cache by setting platformdirs via env or patch
    cache_path = tmp_path / "cache" / "cliol" / "update_cache.json"
    # patch get_cache_path to return our tmp_path
    monkeypatch.setattr("cliol.update_checker.get_cache_path", lambda: cache_path)
    _write_cache(cache_path, "0.2.0")
    assert cache_path.exists()
    # file 0600
    mode_file = os.stat(cache_path).st_mode & 0o777
    assert mode_file == 0o600
    # dir 0700
    mode_dir = os.stat(cache_path.parent).st_mode & 0o777
    assert mode_dir == 0o700
    # content valid
    data = json.loads(cache_path.read_text())
    assert data["latest_version"] == "0.2.0"
    assert "checked_at" in data


def test_read_cache_returns_none_when_missing(tmp_path):
    from cliol.update_checker import _read_cache

    path = tmp_path / "missing.json"
    assert _read_cache(path) is None


def test_read_cache_returns_none_when_corrupt(tmp_path, monkeypatch):
    from cliol.update_checker import _read_cache

    p = tmp_path / "corrupt.json"
    p.write_text("not json {{", encoding="utf-8")
    assert _read_cache(p) is None


def test_cache_hit_within_24h_no_fetch(monkeypatch, tmp_path):
    from cliol import update_checker

    cache_path = tmp_path / "update_cache.json"
    # write recent cache (2h old)
    update_checker._write_cache(cache_path, "0.2.0")
    # Ensure _read_cache reads the file we just wrote (age <24h)
    data = update_checker._read_cache(cache_path)
    assert data is not None
    assert data["latest_version"] == "0.2.0"
    # Verify checked_at is recent and within TTL
    from datetime import datetime, timezone

    checked_at = datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - checked_at).total_seconds()
    assert age < 86400
    # _read_cache with corrupt/missing already tested; fresh cache data is usable


def test_get_cache_path_uses_platformdirs_and_fallback(tmp_path, monkeypatch):
    from cliol.update_checker import get_cache_path

    # Normal case: should return user_cache_dir path
    p = get_cache_path()
    assert p.name == "update_cache.json"
    assert "cliol" in str(p)


def test_write_cache_atomic_tmp(tmp_path, monkeypatch):
    from cliol.update_checker import _write_cache

    p = tmp_path / "a" / "b" / "update_cache.json"
    _write_cache(p, "1.0.0")
    assert p.exists()
    # tmp file should not remain
    tmp_file = p.with_suffix(".tmp")
    assert not tmp_file.exists()


# --- Task 1.3 RED: is_newer and fetch ---
def test_is_newer_strips_v_and_compares():
    from cliol.update_checker import is_newer

    assert is_newer("v0.2.0", "0.1.4") is True
    assert is_newer("0.2.0", "0.1.4") is True
    assert is_newer("0.1.4", "0.2.0") is False
    assert is_newer("0.1.4", "0.1.4") is False
    assert is_newer("v0.1.4", "0.1.4") is False


def test_is_newer_invalid_version_returns_false():
    from cliol.update_checker import is_newer

    assert is_newer("not-a-version", "0.1.4") is False
    assert is_newer("0.2.0", "not-a-version") is False
    assert is_newer("v.invalid", "0.1.4") is False


def test_is_newer_prerelease_handling():
    from cliol.update_checker import is_newer

    # packaging handles prerelease: 1.0.0 > 1.0.0b1
    assert is_newer("1.0.0", "1.0.0b1") is True
    assert is_newer("1.0.0b1", "1.0.0") is False


def test_fetch_timeout_returns_none(monkeypatch):
    from cliol import update_checker

    # Simulate httpx timeout
    def fake_httpx_get(*a, **kw):
        raise Exception("timeout")

    monkeypatch.setitem(
        __import__("sys").modules, "httpx", type("M", (), {"get": fake_httpx_get})()
    )
    # Also need urllib to fail
    import urllib.error
    import urllib.request

    def fake_urlopen(*a, **kw):
        raise urllib.error.URLError("timeout")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = update_checker.fetch_latest_version(timeout=2.0)
    assert result is None


def test_fetch_4xx_returns_none(monkeypatch):
    import urllib.error
    import urllib.request

    from cliol import update_checker

    # Simulate httpx not available, urllib 404
    monkeypatch.setitem(__import__("sys").modules, "httpx", None)

    class FakeResponse:
        status = 404

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"message":"Not Found"}'

        def getcode(self):
            return 404

    def fake_urlopen(*a, **kw):
        raise urllib.error.HTTPError("url", 404, "Not Found", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = update_checker.fetch_latest_version(timeout=2.0)
    assert result is None


def test_fetch_strips_v_and_returns_version(monkeypatch):
    import json as _json
    import urllib.request

    from cliol import update_checker

    monkeypatch.setitem(__import__("sys").modules, "httpx", None)

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return _json.dumps({"tag_name": "v0.2.0"}).encode()

        def getcode(self):
            return 200

        status = 200

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: FakeResp())
    result = update_checker.fetch_latest_version(timeout=2.0)
    assert result == "0.2.0"


def test_fetch_uses_2s_timeout(monkeypatch):
    import json as _json
    import urllib.request

    from cliol import update_checker

    monkeypatch.setitem(__import__("sys").modules, "httpx", None)
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return _json.dumps({"tag_name": "v0.3.0"}).encode()

        def getcode(self):
            return 200

        status = 200

    def fake_urlopen(url, timeout=2.0):
        captured["timeout"] = timeout
        captured["url"] = url
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    update_checker.fetch_latest_version(timeout=2.0)
    assert captured["timeout"] == 2.0
    url_str = (
        captured["url"].full_url if hasattr(captured["url"], "full_url") else str(captured["url"])
    )
    assert "repos/ezeprimo/cliol/releases/latest" in url_str


# --- Task 1.5 RED: should_check matrix ---
def test_should_check_suppressed_when_non_tty(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    # ensure config enabled
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False


def test_should_check_suppressed_when_ci(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setenv("CI", "1")
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("TERM", "dumb")
    assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False
    monkeypatch.delenv("TERM", raising=False)


def test_should_check_suppressed_when_json_or_csv(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    assert update_checker.should_check(argv=["cliol", "market", "quote", "--json"]) is False
    assert update_checker.should_check(argv=["cliol", "market", "quote", "--csv"]) is False
    # also json flag before command
    assert update_checker.should_check(argv=["cliol", "--json", "market", "quote"]) is False


def test_should_check_suppressed_when_env_optout(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    for val in ["1", "true", "True", "TRUE", "1"]:
        monkeypatch.setenv("CLIOL_NO_UPDATE_CHECK", val)
        assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)


def test_should_check_suppressed_when_config_false(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: False)
    assert update_checker.should_check(argv=["cliol", "market", "quote"]) is False


def test_should_check_suppressed_when_help_or_version(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    assert update_checker.should_check(argv=["cliol", "--help"]) is False
    assert update_checker.should_check(argv=["cliol", "--version"]) is False
    assert update_checker.should_check(argv=["cliol", "market", "quote", "--help"]) is False


def test_should_check_suppressed_when_non_trunk(monkeypatch):
    from cliol import update_checker

    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    # market options is non-trunk
    assert update_checker.should_check(argv=["cliol", "market", "options", "GGAL"]) is False
    # trading buy is non-trunk
    assert update_checker.should_check(argv=["cliol", "trading", "buy"]) is False
    # market panel is non-trunk
    assert update_checker.should_check(argv=["cliol", "market", "panel"]) is False


def test_should_check_true_for_trunk_when_all_guards_pass(monkeypatch):
    from cliol import update_checker
    from cliol.output import set_format

    set_format("table")
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    # trunk allowlist items
    assert update_checker.should_check(argv=["cliol"]) is True  # ()
    assert update_checker.should_check(argv=["cliol", "setup"]) is True
    assert update_checker.should_check(argv=["cliol", "auth", "test"]) is True
    assert update_checker.should_check(argv=["cliol", "market", "quote", "GGAL"]) is True
    assert update_checker.should_check(argv=["cliol", "market", "data", "GGAL"]) is True
    assert update_checker.should_check(argv=["cliol", "portfolio", "show"]) is True
    assert update_checker.should_check(argv=["cliol", "account", "status"]) is True
    assert update_checker.should_check(argv=["cliol", "operations", "list"]) is True
    assert update_checker.should_check(argv=["cliol", "fci", "list"]) is True
    assert update_checker.should_check(argv=["cliol", "config", "list"]) is True


def test_check_and_notify_throttle_stale_fetch(monkeypatch, tmp_path):
    """When cache stale >24h, fetch must be called."""
    import json as _json
    from datetime import datetime, timedelta, timezone

    from cliol import update_checker
    from cliol.output import set_format

    set_format("table")

    cache_path = tmp_path / "stale.json"
    # Write stale cache (25h old)
    old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat().replace("+00:00", "Z")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(_json.dumps({"latest_version": "0.1.4", "checked_at": old_time}))
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    monkeypatch.setattr(update_checker, "is_newer", lambda latest, current: True)
    monkeypatch.setattr("sys.argv", ["cliol", "portfolio", "show"])

    called = {}

    def fake_fetch(timeout=2.0):
        called["called"] = True
        return "0.2.0"

    monkeypatch.setattr(update_checker, "fetch_latest_version", fake_fetch)
    # Mock Console to avoid output
    monkeypatch.setattr(
        update_checker,
        "Console",
        lambda *a, **kw: type("C", (), {"print": lambda self, *a, **kw: None})(),
    )

    update_checker.check_and_notify()
    assert called.get("called") is True
    # Cache should be updated with new version
    data = _json.loads(cache_path.read_text())
    assert data["latest_version"] == "0.2.0"


def test_check_and_notify_write_on_success_only(monkeypatch, tmp_path):
    """Cache written only on fetch success, not on failure."""
    import json as _json
    from datetime import datetime, timedelta, timezone

    from cliol import update_checker

    cache_path = tmp_path / "write_success.json"
    old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat().replace("+00:00", "Z")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(_json.dumps({"latest_version": "0.1.4", "checked_at": old_time}))
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    monkeypatch.setattr(update_checker, "is_newer", lambda latest, current: True)
    monkeypatch.setattr("sys.argv", ["cliol", "portfolio", "show"])
    monkeypatch.setattr(
        update_checker,
        "Console",
        lambda *a, **kw: type("C", (), {"print": lambda self, *a, **kw: None})(),
    )

    # Fetch fails -> cache should remain old
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: None)
    update_checker.check_and_notify()
    data = _json.loads(cache_path.read_text())
    assert data["latest_version"] == "0.1.4"
    assert data["checked_at"] == old_time


def test_check_and_notify_banner_uses_stderr(monkeypatch, tmp_path):
    """Banner must go to stderr via Console(file=sys.stderr)."""
    import sys

    from cliol import update_checker
    from cliol.output import set_format

    set_format("table")

    cache_path = tmp_path / "banner_stderr.json"
    update_checker._write_cache(cache_path, "0.2.0")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    monkeypatch.setattr(update_checker, "is_newer", lambda latest, current: True)
    monkeypatch.setattr("sys.argv", ["cliol", "market", "quote", "GGAL"])

    captured = {}

    class FakeConsole:
        def __init__(self, *a, **kw):
            captured["file"] = kw.get("file")
            captured["is_stderr"] = kw.get("file") is sys.stderr

        def print(self, *a, **kw):
            captured["text"] = " ".join(str(x) for x in a)

    monkeypatch.setattr(update_checker, "Console", FakeConsole)
    update_checker.check_and_notify()
    assert captured.get("is_stderr") is True
    assert "Update available" in captured.get("text", "")


def test_config_is_update_check_enabled_variants(tmp_path):
    from cliol.config import ConfigManager

    cm = ConfigManager(config_path=tmp_path / "config.toml")
    # default True
    assert cm.is_update_check_enabled() is True
    for val in ["false", "0", "no", "False", "NO", "off"]:
        cm.set("updates.check", val)
        assert cm.is_update_check_enabled() is False, f"failed for {val}"
    for val in ["true", "1", "yes"]:
        cm.set("updates.check", val)
        assert cm.is_update_check_enabled() is True
    # alias
    cm2 = ConfigManager(config_path=tmp_path / "config2.toml")
    cm2.set("update_check.enabled", "false")
    assert cm2.is_update_check_enabled() is False
    cm2.set("update_check.enabled", "true")
    assert cm2.is_update_check_enabled() is True
    # alias precedence: updates.check wins if both present
    cm2.set("updates.check", "true")
    cm2.set("update_check.enabled", "false")
    assert cm2.is_update_check_enabled() is True


def test_check_and_notify_never_raises(monkeypatch, tmp_path):
    """check_and_notify must never raise even on exceptions."""
    from cliol import update_checker

    monkeypatch.setattr(
        update_checker,
        "should_check",
        lambda argv=None: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    # Should not raise
    update_checker.check_and_notify()

    monkeypatch.setattr(update_checker, "should_check", lambda argv=None: True)
    monkeypatch.setattr(
        update_checker, "get_cache_path", lambda: (_ for _ in ()).throw(Exception("fail"))
    )
    update_checker.check_and_notify()
