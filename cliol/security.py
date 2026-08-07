"""Contraseña de gastos: hashing bcrypt, verificación y ciclo de vida."""

import bcrypt

__all__ = ["SpendingPassword"]

MIN_LENGTH = 4
ERROR_TOO_SHORT = "La contraseña debe tener al menos 4 caracteres."
ERROR_WRONG_CURRENT = "Contraseña actual incorrecta."


def _hash(plain: str) -> str:
    """Devuelve el hash bcrypt (prefijo $2b$) con sal aleatoria."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class SpendingPassword:
    """Operaciones de la contraseña de gastos basadas en bcrypt."""

    @staticmethod
    def create(plain: str) -> str:
        """Crea el hash de una nueva contraseña (mínimo 4 caracteres)."""
        if plain is None or len(plain) < MIN_LENGTH:
            raise ValueError(ERROR_TOO_SHORT)
        return _hash(plain)

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        """Verifica una contraseña contra su hash."""
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except ValueError:
            return False

    @staticmethod
    def change(old: str, new: str, current_hash: str) -> str:
        """Cambia la contraseña validando la actual; devuelve el nuevo hash."""
        if not SpendingPassword.verify(old, current_hash):
            raise ValueError(ERROR_WRONG_CURRENT)
        return SpendingPassword.create(new)

    @staticmethod
    def clear(config: dict) -> bool:
        """Elimina el hash de la sección [trading]; True si se eliminó algo."""
        trading = config.get("trading")
        if not isinstance(trading, dict) or "password_hash" not in trading:
            return False
        del trading["password_hash"]
        return True
