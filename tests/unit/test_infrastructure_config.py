import time

import jwt
import pytest

from src.infrastructure.config import JWTTokenGenerator


def test_jwt_configuracion_desde_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "secreto-de-prueba-suficientemente-largo-2026")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRATION_HOURS", "2")
    monkeypatch.setenv("ENVIRONMENT", "development")

    token = JWTTokenGenerator.generar_jwt(
        id_usuario="USR-TAMBO-001",
        correo="evaluador@eltambo.gob.pe",
        rol="EVALUADOR_LICENCIAS",
    )
    payload = jwt.decode(
        token,
        "secreto-de-prueba-suficientemente-largo-2026",
        algorithms=["HS256"],
    )

    assert payload["sub"] == "USR-TAMBO-001"
    assert payload["email"] == "evaluador@eltambo.gob.pe"
    assert payload["role"] == "EVALUADOR_LICENCIAS"
    assert 7000 <= payload["exp"] - int(time.time()) <= 7300


def test_jwt_falla_sin_secreto_en_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("RENDER", raising=False)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        JWTTokenGenerator.generar_jwt(
            id_usuario="USR-TAMBO-001",
            correo="evaluador@eltambo.gob.pe",
            rol="EVALUADOR_LICENCIAS",
        )


def test_jwt_valida_horas_de_expiracion(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "secreto-de-prueba-suficientemente-largo-2026")
    monkeypatch.setenv("JWT_EXPIRATION_HOURS", "invalido")

    with pytest.raises(RuntimeError, match="entero"):
        JWTTokenGenerator.generar_jwt("USR-1", "user@eltambo.gob.pe", "EVALUADOR_LICENCIAS")

    monkeypatch.setenv("JWT_EXPIRATION_HOURS", "0")
    with pytest.raises(RuntimeError, match="mayor a 0"):
        JWTTokenGenerator.generar_jwt("USR-1", "user@eltambo.gob.pe", "EVALUADOR_LICENCIAS")


def test_jwt_usa_fallback_solo_en_desarrollo(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    token = JWTTokenGenerator.generar_jwt(
        id_usuario="USR-TAMBO-002",
        correo="mesadepartes@eltambo.gob.pe",
        rol="MESA_DE_PARTES",
    )
    payload = jwt.decode(
        token,
        JWTTokenGenerator._DEV_FALLBACK_SECRET,
        algorithms=["HS256"],
    )

    assert payload["sub"] == "USR-TAMBO-002"
    assert payload["role"] == "MESA_DE_PARTES"
