import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from dotenv import load_dotenv

from src.application.ports.output_ports import VerificadorTokenPort

load_dotenv()


class JWTTokenGenerator:
    """Generador de tokens JWT firmados con HMAC-SHA256 (Cumplimiento Ley N.° 29733)."""

    _DEV_FALLBACK_SECRET = secrets.token_urlsafe(48)
    _HASH_ALGORITMO = "pbkdf2_sha256"
    _HASH_ITERACIONES = 210000

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
    def es_produccion(cls) -> bool:
        entorno = os.getenv("ENVIRONMENT", "development").strip().lower()
        return entorno in {"production", "prod", "staging"} or bool(os.getenv("RENDER"))

    @classmethod
    def validar_configuracion_produccion(cls) -> None:
        if not cls.es_produccion():
            return
        secreto = os.getenv("JWT_SECRET_KEY", "").strip()
        if not secreto:
            raise RuntimeError("JWT_SECRET_KEY es obligatoria en staging/producción.")
        if len(secreto) < 32:
            raise RuntimeError("JWT_SECRET_KEY debe tener al menos 32 caracteres en producción.")
        for nombre in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SECRET_KEY"):
            if not os.getenv(nombre, "").strip():
                raise RuntimeError(f"{nombre} es obligatoria en staging/producción.")

    @classmethod
    def generar_hash_password(cls, password_plano: str) -> str:
        sal = secrets.token_bytes(16)
        derivado = hashlib.pbkdf2_hmac(
            "sha256",
            password_plano.encode("utf-8"),
            sal,
            cls._HASH_ITERACIONES,
        )
        return "$".join(
            (
                cls._HASH_ALGORITMO,
                str(cls._HASH_ITERACIONES),
                base64.urlsafe_b64encode(sal).decode("ascii"),
                base64.urlsafe_b64encode(derivado).decode("ascii"),
            )
        )

    @classmethod
    def verificar_password(cls, password_plano: str, password_hash: str) -> bool:
        try:
            algoritmo, iteraciones_texto, sal_texto, derivado_texto = str(password_hash).split("$", 3)
            if algoritmo != cls._HASH_ALGORITMO:
                return False
            iteraciones = int(iteraciones_texto)
            if iteraciones <= 0:
                return False
            sal = base64.urlsafe_b64decode(sal_texto.encode("ascii"))
            derivado_esperado = base64.urlsafe_b64decode(derivado_texto.encode("ascii"))
        except (ValueError, TypeError, UnicodeEncodeError):
            return False

        derivado_calculado = hashlib.pbkdf2_hmac(
            "sha256",
            password_plano.encode("utf-8"),
            sal,
            iteraciones,
        )
        return hmac.compare_digest(derivado_calculado, derivado_esperado)

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

    @classmethod
    def verificar_jwt(cls, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                cls._secret_key(),
                algorithms=[cls._algorithm()],
            )
        except jwt.ExpiredSignatureError as error:
            raise PermissionError("El token JWT expiró.") from error
        except jwt.InvalidTokenError as error:
            raise PermissionError("El token JWT es inválido.") from error


class JWTTokenVerifier(VerificadorTokenPort):
    """Implementación del puerto de verificación de tokens (PMV3-1-HU09)."""

    def verificar_token(self, token: str) -> Dict[str, Any]:
        return JWTTokenGenerator.verificar_jwt(token)
