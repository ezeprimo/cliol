"""Unit tests for the cliol error hierarchy and exit codes."""

import pytest

from cliol.errors import (
    APIError,
    AuthError,
    CliolError,
    ConfigError,
    NetworkError,
    TradingDisabled,
    WrongSpendingPassword,
)


def test_base_error_default_exit_code_and_message():
    err = CliolError("boom")
    assert err.exit_code == 1
    assert str(err) == "boom"


@pytest.mark.parametrize(
    "exc_cls, expected_code",
    [
        (ConfigError, 1),
        (APIError, 1),
        (NetworkError, 2),
        (AuthError, 3),
        (WrongSpendingPassword, 4),
        (TradingDisabled, 5),
    ],
)
def test_exit_codes_per_spec(exc_cls, expected_code):
    assert exc_cls("x").exit_code == expected_code


def test_all_are_cliol_error_subclasses():
    for cls in (ConfigError, APIError, NetworkError, AuthError, WrongSpendingPassword, TradingDisabled):
        assert issubclass(cls, CliolError)


def test_message_passed_through_str():
    err = TradingDisabled("Operatoria deshabilitada.")
    assert err.exit_code == 5
    assert str(err) == "Operatoria deshabilitada."


def test_wrong_spending_password_message():
    assert str(WrongSpendingPassword("Contraseña de gastos incorrecta.")) == "Contraseña de gastos incorrecta."
