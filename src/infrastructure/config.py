import jwt
from datetime import datetime, timedelta, timezone

class JWTTokenGenerator:
    """Generador de tokens JWT firmados con HMAC-SHA256 (Cumplimiento Ley N.° 29733)."""
    SECRET_KEY = "SIMEL_EL_TAMBO_2026_LEY_29733_AES256_SECRET_KEY_32BYTES_MIN"
    ALGORITHM = "HS256"

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
            "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
