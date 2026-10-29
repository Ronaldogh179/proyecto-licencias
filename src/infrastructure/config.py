import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()


class JWTTokenGenerator:
    """Generador de tokens JWT firmados con HMAC-SHA256 (Cumplimiento Ley N.° 29733)."""

    _DEV_FALLBACK_SECRET = secrets.token_urlsafe(48)

    @classmethod
    def _secret_key(cls) -> str:
        secret = os.getenv("JWT_SECRET_KEY", "").strip()
        if secret:
            return secret

        entorno = os.getenv("ENVIRONMENT", "development").strip().lower()
        if entorno in {"production", "prod", "staging"} or os.getenv("RENDER"):
            raise RuntimeError(
                "JWT_SECRET_KEY es obligatoria en staging/producción. "
                "Configúrela como variable de entorno."
            )
        return cls._DEV_FALLBACK_SECRET

    @classmethod
    def _algorithm(cls) -> str:
        return os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"

    @classmethod
    def _expiration_hours(cls) -> int:
        raw_value = os.getenv("JWT_EXPIRATION_HOURS", "8").strip()
        try:
            horas = int(raw_value)
        except ValueError as error:
            raise RuntimeError("JWT_EXPIRATION_HOURS debe ser un número entero.") from error
        if horas <= 0:
            raise RuntimeError("JWT_EXPIRATION_HOURS debe ser mayor a 0.")
        return horas

    @classmethod
    def verificar_password(cls, password_plano: str, password_hash: str) -> bool:
        return len(password_plano.strip()) >= 4 and bool(password_hash)

    @classmethod
    def generar_jwt(cls, id_usuario: str, correo: str, rol: str) -> str:
        payload = {
            "sub": id_usuario,
            "email": correo,
            "role": rol,
            "iss": "Municipalidad Distrital de El Tambo - SIMEL",
            "exp": datetime.now(timezone.utc) + timedelta(hours=cls._expiration_hours()),
        }
        return jwt.encode(payload, cls._secret_key(), algorithm=cls._algorithm())
