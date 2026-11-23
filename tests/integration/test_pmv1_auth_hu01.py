import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi.testclient import TestClient

from src.infrastructure.main import app

client = TestClient(app)
PASSWORD_DEMO = "municipal2026"
PDF_DIGITAL = Path("muestras_pdf_tupa/EXP-2026-0351_OBSERVADO.pdf")


def _login_sin_rol(correo: str = "evaluador@eltambo.gob.pe") -> dict:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": PASSWORD_DEMO},
    )
    assert respuesta.status_code == 200
    return respuesta.json()["data"]


def test_login_sin_rol_deriva_rol_desde_la_cuenta():
    data = _login_sin_rol()
    assert data["rol"] == "EVALUADOR_LICENCIAS"
    assert data["correo"] == "evaluador@eltambo.gob.pe"
    assert data["usuario"]
    assert data["access_token"]


def test_login_con_password_incorrecta_devuelve_401():
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"correo": "evaluador@eltambo.gob.pe", "password": "incorrecta"},
    )
    assert respuesta.status_code == 401
    assert "Contraseña incorrecta" in respuesta.json()["detail"]


def test_acceso_sin_sesion_y_token_vencido_devuelven_401():
    sin_token = client.get("/api/v1/expedientes/bandeja")
    assert sin_token.status_code == 401

    payload = {
        "sub": "USR-TAMBO-001",
        "email": "evaluador@eltambo.gob.pe",
        "role": "EVALUADOR_LICENCIAS",
        "iss": "Municipalidad Distrital de El Tambo - SIMEL",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    token_vencido = jwt.encode(
        payload,
        os.environ["JWT_SECRET_KEY"],
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )
    respuesta = client.get(
        "/api/v1/expedientes/bandeja",
        headers={"Authorization": f"Bearer {token_vencido}"},
    )
    assert respuesta.status_code == 401
    assert "expir" in respuesta.json()["detail"].lower()


def test_carga_de_pdf_despues_del_login():
    data = _login_sin_rol()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    codigo = "EXP-2026-HU01-PDF"
    respuesta = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data={
            "codigo_expediente": codigo,
            "dni_ruc_titular": "20601122334",
            "razon_social_nombre": "Restaurante Demo HU01 S.A.C.",
            "giro_comercial": "Restaurante",
            "tipo_tramite": "Nueva licencia",
            "direccion_predio": "Av. Demo 123 - El Tambo",
            "area_comercial_m2": "110.5",
            "modo_indicadores": "automatico",
            "algoritmo": "xgboost",
        },
        files={
            "archivo_pdf": (
                "expediente_hu01.pdf",
                PDF_DIGITAL.read_bytes(),
                "application/pdf",
            )
        },
    )
    assert respuesta.status_code == 200
    expediente = respuesta.json()["expediente"]
    assert expediente["codigo_expediente"] == codigo
    assert expediente["evaluacion_riesgo"]["nivel_riesgo"] in {"ALTO", "MEDIO", "BAJO"}
    assert expediente["texto_extraido_completo"]
