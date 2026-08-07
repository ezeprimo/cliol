"""Integration smoke tests: root help, group help, command help, global flags."""

import re

from typer.testing import CliRunner

from cliol.main import app

# Rich outputs ANSI codes even in CliRunner on some platforms — strip them
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _clean(output: str) -> str:
    return _ANSI_RE.sub("", output)


GROUPS = [
    "market",
    "portfolio",
    "fci",
    "mep",
    "cpd",
    "trading",
    "advisor",
    "auth",
    "config",
    "security",
]


def test_root_help_lists_all_groups():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    out = _clean(result.output)
    for group in GROUPS:
        assert group in out


def test_root_help_lists_setup_command():
    result = CliRunner().invoke(app, ["--help"])
    assert "setup" in _clean(result.output)


def test_group_help_lists_subcommands():
    result = CliRunner().invoke(app, ["market", "--help"])
    assert result.exit_code == 0
    out = _clean(result.output)
    for sub in [
        "quote",
        "data",
        "options",
        "instruments",
        "massive",
        "panel",
        "detail",
        "mep-rate",
    ]:
        assert sub in out


def test_command_help_shows_arguments_and_global_flags():
    result = CliRunner().invoke(app, ["market", "quote", "--help"])
    assert result.exit_code == 0
    out = _clean(result.output)
    for flag in ["symbol", "--json", "--csv", "--verbose", "--debug", "--market", "--term"]:
        assert flag in out


def test_help_for_gated_command_group():
    result = CliRunner().invoke(app, ["trading", "--help"])
    assert result.exit_code == 0
    out = _clean(result.output)
    for sub in ["buy", "sell", "buy-usd", "sell-usd", "cancel"]:
        assert sub in out


def test_help_for_auth_config_security():
    for group, subs in {
        "auth": ["test"],
        "config": ["set", "get", "list", "trading"],
        "security": ["set-password", "change-password", "clear-password"],
    }.items():
        result = CliRunner().invoke(app, [group, "--help"])
        assert result.exit_code == 0
        out = _clean(result.output)
        for sub in subs:
            assert sub in out
