"""Unit tests for SpendingPassword: bcrypt hashing, verification, change, clear."""

import pytest

from cliol.security import SpendingPassword


def test_create_returns_bcrypt_hash_with_2b_prefix():
    hashed = SpendingPassword.create("secreto")
    assert hashed.startswith("$2b$")
    assert "secreto" not in hashed


def test_verify_correct_password():
    hashed = SpendingPassword.create("secreto")
    assert SpendingPassword.verify("secreto", hashed) is True


def test_verify_wrong_password():
    hashed = SpendingPassword.create("secreto")
    assert SpendingPassword.verify("incorrecta", hashed) is False


def test_create_rejects_short_password():
    with pytest.raises(ValueError) as exc:
        SpendingPassword.create("abc")
    assert "La contraseña debe tener al menos 4 caracteres." in str(exc.value)


def test_create_accepts_minimum_4_chars():
    assert SpendingPassword.verify("abcd", SpendingPassword.create("abcd"))


def test_unique_salt_generates_different_hashes():
    h1 = SpendingPassword.create("secreto")
    h2 = SpendingPassword.create("secreto")
    assert h1 != h2
    assert SpendingPassword.verify("secreto", h1)
    assert SpendingPassword.verify("secreto", h2)


def test_change_with_correct_current_password():
    old_hash = SpendingPassword.create("vieja123")
    new_hash = SpendingPassword.change("vieja123", "nueva123", old_hash)
    assert new_hash.startswith("$2b$")
    assert SpendingPassword.verify("nueva123", new_hash)
    assert not SpendingPassword.verify("vieja123", new_hash)


def test_change_with_wrong_current_password_raises():
    old_hash = SpendingPassword.create("vieja123")
    with pytest.raises(ValueError) as exc:
        SpendingPassword.change("incorrecta", "nueva123", old_hash)
    assert "Contraseña actual incorrecta." in str(exc.value)
    # Old hash unchanged and still verifies the old password
    assert SpendingPassword.verify("vieja123", old_hash)


def test_clear_removes_hash_from_config():
    config = {"trading": {"enabled": True, "password_hash": "$2b$12$abc"}}
    assert SpendingPassword.clear(config) is True
    assert "password_hash" not in config["trading"]


def test_clear_without_hash_returns_false():
    config = {"trading": {"enabled": False}}
    assert SpendingPassword.clear(config) is False


def test_clear_handles_missing_trading_section():
    config = {"iol": {"username": "u"}}
    assert SpendingPassword.clear(config) is False
    assert "trading" not in config
