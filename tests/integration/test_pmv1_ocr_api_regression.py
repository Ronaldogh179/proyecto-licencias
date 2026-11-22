from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from src.infrastructure.main import app

client = TestClient(app)
PDF_DIGITAL = Path("muestras_pdf_tupa/EXP-2026-0351_OBSERVADO.pdf")


def _login(correo: str = "evaluador@eltambo.gob.pe", rol: str = "EVALUADOR_LICENCIAS") -> dict:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={"correo": correo, "password": "municipal2026", "rol": rol},
    )
    assert respuesta.status_code == 200
    return {"Authorization": f"Bearer {respuesta.json()['data']['access_token']}"}


def _datos_expediente(codigo: str, modo: str) -> dict:
    return {
        "codigo_expediente": codigo,
        "dni_ruc_titular": "20601122334",
        "razon_social_nombre": "Restaurante Demo S.A.C.",
        "giro_comercial": "Restaurante",
        "tipo_tramite": "Nueva licencia",
        "direccion_predio": "Av. Demo 123 - El Tambo",
        "area_comercial_m2": "110.5",
        "modo_indicadores": modo,
        "documentos_faltantes": "3",
        "inconsistencias_detectadas": "3",
        "documento_critico_faltante": "0",
        "algoritmo": "xgboost",
    }


def _pdf_protegido() -> bytes:
    documento = pymupdf.open()
    pagina = documento.new_page()
    pagina.insert_text((72, 72), "Documento protegido")
    contenido = documento.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="propietario",
        user_pw="secreto",
    )
    documento.close()
    return contenido


def test_evaluar_rechaza_pdf_vacio_danado_y_protegido():
    headers = _login()

    respuesta_vacio = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-VACIO", "automatico"),
        files={"archivo_pdf": ("vacio.pdf", b"", "application/pdf")},
    )
    assert respuesta_vacio.status_code == 422
    assert "vacío" in respuesta_vacio.json()["detail"]

    respuesta_danado = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-DANADO", "automatico"),
        files={"archivo_pdf": ("danado.pdf", b"%PDF-1.4 roto", "application/pdf")},
    )
    assert respuesta_danado.status_code == 422
    assert "dañado" in respuesta_danado.json()["detail"]

    respuesta_protegido = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-PROTEGIDO", "automatico"),
        files={"archivo_pdf": ("protegido.pdf", _pdf_protegido(), "application/pdf")},
    )
    assert respuesta_protegido.status_code == 422
    assert "contraseña" in respuesta_protegido.json()["detail"]


def test_evaluar_modo_automatico_ignora_manuales_y_devuelve_metricas_reales():
    headers = _login()

    respuesta = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-AUTO", "automatico"),
        files={
            "archivo_pdf": (
                "EXP-2026-0351_OBSERVADO.pdf",
                PDF_DIGITAL.read_bytes(),
                "application/pdf",
            )
        },
    )

    assert respuesta.status_code == 200
    expediente = respuesta.json()["expediente"]
    assert expediente["documentos_faltantes"] == 0
    assert expediente["inconsistencias_detectadas"] == 0
    assert expediente["documento_critico_faltante"] == 1
    assert expediente["confianza_ocr"] == 100.0
    assert "DECLARACION JURADA" in expediente["texto_extraido_completo"]
    metadatos = expediente["metadatos_ocr"]
    assert metadatos["tipo_extraccion"] == "digital"
    assert metadatos["paginas_totales"] == 1
    assert metadatos["modo_indicadores"] == "automatico"
    assert set(metadatos["indicadores_estimados"]) == {
        "documentos_faltantes",
        "inconsistencias_detectadas",
        "documento_critico_faltante",
    }


def test_evaluar_modo_manual_respeta_los_valores_del_evaluador():
    headers = _login()

    respuesta = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-MANUAL", "manual"),
        files={
            "archivo_pdf": (
                "EXP-2026-0351_OBSERVADO.pdf",
                PDF_DIGITAL.read_bytes(),
                "application/pdf",
            )
        },
    )

    assert respuesta.status_code == 200
    expediente = respuesta.json()["expediente"]
    assert expediente["documentos_faltantes"] == 3
    assert expediente["inconsistencias_detectadas"] == 3
    assert expediente["documento_critico_faltante"] == 0
    assert expediente["metadatos_ocr"]["modo_indicadores"] == "manual"
    assert expediente["metadatos_ocr"]["indicadores_estimados"] == []


def test_evaluar_exige_sesion_valida_y_rol_autorizado():
    respuesta_sin_token = client.post(
        "/api/v1/expedientes/evaluar",
        data=_datos_expediente("EXP-OCR-SIN-TOKEN", "automatico"),
    )
    assert respuesta_sin_token.status_code == 401

    headers_mesa = _login("mesadepartes@eltambo.gob.pe", "MESA_DE_PARTES")
    respuesta_mesa = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers_mesa,
        data=_datos_expediente("EXP-OCR-MESA", "automatico"),
    )
    assert respuesta_mesa.status_code == 403
    assert "permisos" in respuesta_mesa.json()["detail"]


def test_evaluar_rechaza_modo_indicadores_invalido():
    headers = _login()

    respuesta = client.post(
        "/api/v1/expedientes/evaluar",
        headers=headers,
        data=_datos_expediente("EXP-OCR-MODO-INVALIDO", "inventado"),
    )
    assert respuesta.status_code == 422
    assert "modo_indicadores" in respuesta.json()["detail"]
