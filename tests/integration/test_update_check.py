"""Integration tests for update check: banner + command."""

import json

import pytest
from typer.testing import CliRunner

from cliol.main import app


@pytest.fixture(autouse=True)
def _reset_output_format():
    from cliol.output import set_format

    set_format("table")
    yield
    set_format("table")


def test_update_check_shows_table_when_newer(monkeypatch):
    import cliol.commands.update as upd
    from cliol import update_checker

    monkeypatch.setattr(upd, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    monkeypatch.setattr(
        upd, "get_cache_path", lambda: __import__("pathlib").Path("/tmp/nonexistent_cache.json")
    )
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    monkeypatch.setattr(
        update_checker,
        "get_cache_path",
        lambda: __import__("pathlib").Path("/tmp/nonexistent_cache.json"),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["update", "check"])
    assert result.exit_code == 0
    # Should show current and latest and instruction
    assert "0.1.4" in result.output or "current" in result.output.lower()
    assert "0.2.0" in result.output


def test_update_check_json(monkeypatch):
    import cliol.commands.update as upd
    from cliol import update_checker

    monkeypatch.setattr(upd, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    monkeypatch.setattr(
        upd, "get_cache_path", lambda: __import__("pathlib").Path("/tmp/nonexistent_cache2.json")
    )
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    monkeypatch.setattr(
        update_checker,
        "get_cache_path",
        lambda: __import__("pathlib").Path("/tmp/nonexistent_cache2.json"),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["update", "check", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["current"] == "0.1.4"
    assert data["latest"] == "0.2.0"
    assert data["update_available"] is True
    # No banner on stderr (result.output includes both? CliRunner captures combined? We check not banner)
    # Banner is to stderr, but CliRunner merges; check that json is pure
    assert "Update available" not in result.output


def test_update_check_force_bypasses_cache(monkeypatch, tmp_path):
    import cliol.commands.update as upd
    from cliol import update_checker

    cache_path = tmp_path / "update_cache.json"
    # Write old cache with 1h old but different version
    update_checker._write_cache(cache_path, "0.1.4")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr(upd, "get_cache_path", lambda: cache_path)
    # First call without force should use cache (0.1.4) => no update
    # But after force, should fetch remote 0.2.0
    called = {}

    def fake_fetch(timeout=2.0):
        called["called"] = True
        return "0.2.0"

    monkeypatch.setattr(update_checker, "fetch_latest_version", fake_fetch)
    monkeypatch.setattr(upd, "fetch_latest_version", fake_fetch)
    runner = CliRunner()
    result_no_force = runner.invoke(app, ["update", "check", "--json"])
    # Without force, should use cached 0.1.4 if fresh (<24h) => update_available False, fetch not called
    assert result_no_force.exit_code == 0
    assert "called" not in called
    # Now with force
    called.clear()
    result2 = runner.invoke(app, ["update", "check", "--json", "--force"])
    assert result2.exit_code == 0
    assert called.get("called") is True
    data = json.loads(result2.output)
    assert data["latest"] == "0.2.0"


def test_update_check_offline_exits_2(monkeypatch):
    import cliol.commands.update as upd
    from cliol import update_checker

    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: None)
    monkeypatch.setattr(
        update_checker,
        "get_cache_path",
        lambda: __import__("pathlib").Path("/tmp/nonexistent_offline.json"),
    )
    monkeypatch.setattr(upd, "fetch_latest_version", lambda timeout=2.0: None)
    monkeypatch.setattr(
        upd, "get_cache_path", lambda: __import__("pathlib").Path("/tmp/nonexistent_offline.json")
    )
    # Ensure no cache
    runner = CliRunner()
    result = runner.invoke(app, ["update", "check"])
    assert result.exit_code == 2
    assert "Error" in result.output


def test_trunk_tty_banner_to_stderr(monkeypatch, tmp_path):

    from cliol import update_checker

    cache_path = tmp_path / "banner_cache.json"
    update_checker._write_cache(cache_path, "0.2.0")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    # Mock is_newer to True
    monkeypatch.setattr(update_checker, "is_newer", lambda latest, current: True)
    # Need should_check true: set TTY, no CI, no json
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    # Capture banner via mocking Console
    captured = {}

    class FakeConsole:
        def __init__(self, *a, **kw):
            captured["file"] = kw.get("file")
            captured["called"] = False

        def print(self, *a, **kw):
            captured["called"] = True
            captured["text"] = " ".join(str(x) for x in a)
            # also write to stderr file if provided
            if captured["file"]:
                try:
                    captured["file"].write(captured["text"])
                except Exception:
                    pass

    monkeypatch.setattr("cliol.update_checker.Console", FakeConsole)
    # Ensure sys.stderr.isatty True via patching the class
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    # Also mock sys.argv
    monkeypatch.setattr("sys.argv", ["cliol", "portfolio", "show"])
    # Need to make check_and_notify see TTY: we patched sys.stderr.isatty globally, but Console patch already captures
    update_checker.check_and_notify()
    assert captured.get("called") is True
    assert "Update available" in captured.get("text", "")
    assert "0.1.4" in captured.get("text", "") or "0.1.4" in str(captured)
    assert "0.2.0" in captured.get("text", "")


def test_non_trunk_no_banner(monkeypatch, tmp_path):
    from cliol import update_checker

    cache_path = tmp_path / "nontrunk_cache.json"
    update_checker._write_cache(cache_path, "0.2.0")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    # Non-trunk should not check
    assert update_checker.should_check(argv=["cliol", "market", "options", "GGAL"]) is False
    # Even if we call check_and_notify with non-trunk argv, no banner
    monkeypatch.setattr("sys.argv", ["cliol", "market", "options", "GGAL"])
    # Also need to ensure fetch not called
    called = {}
    monkeypatch.setattr(
        update_checker,
        "fetch_latest_version",
        lambda timeout=2.0: (called.__setitem__("called", True), "0.2.0")[1],
    )
    # Mock Console to capture
    captured = {}

    class FakeConsole:
        def __init__(self, *a, **kw):
            pass

        def print(self, *a, **kw):
            captured["called"] = True

    monkeypatch.setattr("cliol.update_checker.Console", FakeConsole)
    update_checker.check_and_notify()
    assert "called" not in called
    assert "called" not in captured


def test_json_suppressed_no_banner(monkeypatch, tmp_path):
    from cliol import update_checker

    cache_path = tmp_path / "json_suppress.json"
    update_checker._write_cache(cache_path, "0.2.0")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    assert update_checker.should_check(argv=["cliol", "market", "quote", "--json"]) is False


def test_banner_preserves_exit_code(monkeypatch, tmp_path):
    """Banner must not alter exit 0-5 from commands."""
    from cliol import update_checker

    # Simulate command that raises CliolError with exit 1, banner should not change it
    # We test via CliRunner: invoke a failing command with mocked banner
    cache_path = tmp_path / "exit_cache.json"
    update_checker._write_cache(cache_path, "0.2.0")
    monkeypatch.setattr(update_checker, "get_cache_path", lambda: cache_path)
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "0.2.0")
    monkeypatch.setattr(update_checker, "is_newer", lambda latest, current: True)
    # Make banner trigger
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("CLIOL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_checker, "_is_update_check_enabled", lambda: True)
    # Patch Console to capture
    monkeypatch.setattr(
        update_checker,
        "Console",
        lambda *a, **kw: type("C", (), {"print": lambda self, *a, **kw: None})(),
    )

    runner = CliRunner()
    # Use a command that will fail: config get missing key -> exit 1, but we also check that exit remains 1 not changed by banner
    # The run() finally should still call check_and_notify but not alter exit
    result = runner.invoke(app, ["config", "get", "clave.inexistente"])
    # Should be exit 1 (ConfigError)
    assert result.exit_code == 1
    # Even though should_check would be true for config list but not for config get; let's use trunk command that fails via API?
    # For exit 2 test, mock fetch for banner but also make update check fail?
    # Simpler: ensure that a successful trunk command with banner still exits 0
    monkeypatch.setattr("sys.argv", ["cliol", "config", "list"])
    # config list should succeed exit 0 even with banner
    result2 = runner.invoke(app, ["config", "list"])
    assert result2.exit_code == 0


def test_help_no_banner(monkeypatch):
    """python -m cliol --help must not show banner."""
    from cliol import update_checker

    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "9.9.9")
    # Ensure even if we force banner, help is suppressed
    assert update_checker.should_check(argv=["cliol", "--help"]) is False
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Update available" not in result.output


def test_update_check_json_valid_and_exit2(monkeypatch):
    """update check --json must be valid JSON and exit 2 offline."""
    import json as _json

    import cliol.commands.update as upd
    from cliol import update_checker

    # Valid JSON when success
    monkeypatch.setattr(upd, "fetch_latest_version", lambda timeout=2.0: "0.5.0")
    monkeypatch.setattr(
        upd, "get_cache_path", lambda: __import__("pathlib").Path("/tmp/json_valid_cache.json")
    )
    monkeypatch.setattr(update_checker, "fetch_latest_version", lambda timeout=2.0: "0.5.0")
    monkeypatch.setattr(
        update_checker,
        "get_cache_path",
        lambda: __import__("pathlib").Path("/tmp/json_valid_cache.json"),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["update", "check", "--json"])
    assert result.exit_code == 0
    data = _json.loads(result.output)
    assert "current" in data and "latest" in data and "update_available" in data

    # Offline exit 2
    monkeypatch.setattr(upd, "fetch_latest_version", lambda timeout=2.0: None)
    monkeypatch.setattr(
        upd, "get_cache_path", lambda: __import__("pathlib").Path("/tmp/json_offline_cache.json")
    )
    result2 = runner.invoke(app, ["update", "check", "--json"])
    assert result2.exit_code == 2
