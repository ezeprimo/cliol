"""Prompt interactivo compartido (contraseñas enmascaradas y confirmaciones)."""

import typer
from rich.prompt import Prompt

__all__ = ["ask_text", "ask_password", "ask_int", "confirm"]

PASSWORD_PROMPT_HELP = "Contraseña"


def ask_text(message: str) -> str:
    """Solicita texto por stdin (sin enmascarar)."""
    return Prompt.ask(message)


def ask_int(message: str, default: int = None) -> int:
    """Solicita un entero por stdin con validación básica."""
    return Prompt.ask(message, default=default, show_default=default is not None, convert=int)


def ask_password(message: str) -> str:
    """Solicita una contraseña enmascarada (sin eco en la terminal)."""
    return Prompt.ask(message, password=True)


def confirm(message: str, default: bool = False) -> bool:
    """Pide una confirmación s/n por stdin."""
    return typer.confirm(message, default=default)
