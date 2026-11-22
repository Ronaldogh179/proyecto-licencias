from pathlib import Path
from unittest.mock import MagicMock

import pymupdf
import pytest

from src.adapters.outbound.ocr import tesseract_ocr_adapter as ocr_module
from src.adapters.outbound.ocr.tesseract_ocr_adapter import PyMuPDFTesseractOCRAdapter
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO

PDF_DIGITAL = Path("muestras_pdf_tupa/EXP-2026-0351_OBSERVADO.pdf")


def _dto(pdf_bytes: bytes, **overrides) -> IngresoExpedienteInputDTO:
    valores = {
        "codigo_expediente": "EXP-OCR-TEST",
        "dni_ruc_titular": "20601122334",
        "razon_social_nombre": "Restaurante Demo S.A.C.",
        "giro_comercial": "Restaurante",
        "tipo_tramite": "Nueva licencia",
        "direccion_predio": "Av. Demo 123",
        "area_comercial_m2": 110.5,
        "nombre_archivo_pdf": "expediente.pdf",
        "contenido_pdf_bytes": pdf_bytes,
    }
    valores.update(overrides)
    return IngresoExpedienteInputDTO(**valores)


def _pdf_en_blanco() -> bytes:
    documento = pymupdf.open()
    documento.new_page()
    contenido = documento.tobytes()
    documento.close()
    return contenido


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


def test_ocr_pdf_digital_extrae_texto_real_y_confianza_de_extraccion():
    adapter = PyMuPDFTesseractOCRAdapter()

    resultado = adapter.extraer_variables(_dto(PDF_DIGITAL.read_bytes()))

    assert "DECLARACION JURADA" in resultado.texto_extraido_completo
    assert resultado.texto_resumen.startswith("MUNICIPALIDAD DISTRITAL")
    assert resultado.confianza_ocr == 100.0
    assert resultado.metadatos_ocr["tipo_extraccion"] == "digital"
    assert resultado.metadatos_ocr["paginas_texto_digital"] == 1
    assert resultado.metadatos_ocr["paginas_ocr"] == 0
    assert resultado.documentos_faltantes == 0
    assert resultado.inconsistencias_detectadas == 0
    assert resultado.documento_critico_faltante == 1


def test_ocr_pagina_escaneada_invoca_tesseract_y_calcula_confianza(monkeypatch):
    PyMuPDFTesseractOCRAdapter._idiomas_tesseract.cache_clear()
    fake_tesseract = MagicMock()
    fake_tesseract.get_languages.return_value = ["spa", "eng"]
    fake_tesseract.image_to_data.return_value = {
        "text": ["HOLA", "MUNDO", "20601122334"],
        "conf": ["90", "80", "70"],
    }
    monkeypatch.setattr(ocr_module, "pytesseract", fake_tesseract)

    adapter = PyMuPDFTesseractOCRAdapter()
    resultado = adapter.extraer_variables(_dto(_pdf_en_blanco()))

    fake_tesseract.image_to_data.assert_called_once()
    assert "HOLA MUNDO 20601122334" in resultado.texto_extraido_completo
    assert resultado.confianza_ocr == 80.0
    assert resultado.metadatos_ocr["tipo_extraccion"] == "ocr"
    assert resultado.metadatos_ocr["paginas_ocr"] == 1
    assert resultado.metadatos_ocr["idioma_ocr"] == "spa"
    PyMuPDFTesseractOCRAdapter._idiomas_tesseract.cache_clear()


def test_ocr_pagina_escaneada_sin_tesseract_falla_con_mensaje_claro(monkeypatch):
    PyMuPDFTesseractOCRAdapter._idiomas_tesseract.cache_clear()
    fake_tesseract = MagicMock()
    fake_tesseract.get_languages.return_value = []
    monkeypatch.setattr(ocr_module, "pytesseract", fake_tesseract)

    adapter = PyMuPDFTesseractOCRAdapter()
    with pytest.raises(ValueError, match="Tesseract OCR"):
        adapter.extraer_variables(_dto(_pdf_en_blanco()))
    PyMuPDFTesseractOCRAdapter._idiomas_tesseract.cache_clear()


def test_ocr_respeta_indicadores_manuales_sobre_los_estimados():
    adapter = PyMuPDFTesseractOCRAdapter()

    resultado = adapter.extraer_variables(
        _dto(
            PDF_DIGITAL.read_bytes(),
            documentos_faltantes_manual=3,
            inconsistencias_manual=2,
            documento_critico_manual=0,
        )
    )

    assert resultado.documentos_faltantes == 3
    assert resultado.inconsistencias_detectadas == 2
    assert resultado.documento_critico_faltante == 0
    assert resultado.metadatos_ocr["modo_indicadores"] == "manual"
    assert resultado.metadatos_ocr["indicadores_estimados"] == []


def test_ocr_pdf_danado_falla_con_mensaje_claro():
    adapter = PyMuPDFTesseractOCRAdapter()

    with pytest.raises(ValueError, match="dañado"):
        adapter.extraer_variables(_dto(b"%PDF-1.4 archivo truncado sin estructura"))


def test_ocr_pdf_protegido_con_password_falla_con_mensaje_claro():
    adapter = PyMuPDFTesseractOCRAdapter()

    with pytest.raises(ValueError, match="contraseña"):
        adapter.extraer_variables(_dto(_pdf_protegido()))


def test_ocr_sin_pdf_usa_respaldo_y_confianza_cero():
    adapter = PyMuPDFTesseractOCRAdapter()

    resultado = adapter.extraer_variables(_dto(b""))

    assert resultado.confianza_ocr == 0.0
    assert resultado.metadatos_ocr["tipo_extraccion"] == "simulada"
    assert resultado.metadatos_ocr["advertencias"]
    assert "Declaración Jurada TUPA" in resultado.texto_extraido_completo
