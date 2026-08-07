"""Compuerta de operatoria: bloquea operaciones de fondos en modo consulta.

Dos responsabilidades:
- `check()`: si `trading.enabled` es falso, levanta TradingDisabled (exit 5).
- `prompt_password()`: solicita la contraseña de gastos enmascarada y la valida;
  si es incorrecta, levanta WrongSpendingPassword (exit 4).
"""

import rich.prompt

from cliol.config import ConfigManager
from cliol.errors import TradingDisabled, WrongSpendingPassword
from cliol.security import SpendingPassword

__all__ = ["TradingGate"]

BLOCKED_MESSAGE = "Operatoria deshabilitada. Para operar, ejecute: cliol config trading enable"
WRONG_PASSWORD_MESSAGE = "Contraseña de gastos incorrecta."


class TradingGate:
    """Valida que la operatoria esté habilitada y la contraseña de gastos."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def check(self) -> None:
        """Levanta TradingDisabled si la operatoria está deshabilitada."""
        if not self.config.is_trading_enabled():
            raise TradingDisabled(BLOCKED_MESSAGE)

    def _ask_password(self) -> str:
        return rich.prompt.Prompt.ask("Contraseña de gastos", password=True)

    def prompt_password(self) -> bool:
        """Pide la contraseña de gastos y valida contra el hash guardado."""
        stored = self.config.get_password_hash()
        candidate = self._ask_password()
        if stored is None or not SpendingPassword.verify(candidate, stored):
            raise WrongSpendingPassword(WRONG_PASSWORD_MESSAGE)
        return True
