"""Shared pytest fixtures and path setup for cliol tests."""

import sys
from pathlib import Path

# Make the cliol package importable when running from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from typer.testing import CliRunner

from cliol.main import app


@pytest.fixture()
def cli_runner() -> CliRunner:
    """A Typer CliRunner bound to the cliol app."""
    return CliRunner()


@pytest.fixture()
def invoke(cli_runner):
    """Invoke the cliol CLI with args, returning the CliRunner result."""

    def _invoke(*args: str, input: str = None):
        return cli_runner.invoke(app, list(args), input=input)

    return _invoke
