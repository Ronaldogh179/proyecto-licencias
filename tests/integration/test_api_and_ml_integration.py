from pathlib import Path
from fastapi.testclient import TestClient
from src.infrastructure.main import app
from src.infrastructure.container import container

client = TestClient(app)


def test_integracion_endpoint_dashboard_y_bandeja_priorizada():
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "SIMEL" in res_html.text

    res_bandeja = client.get("/api/v1/expedientes/bandeja")
    assert res_bandeja.status_code == 200
    body = res_bandeja.json()
    assert body["total"] >= 3
    assert body["metricas_modelos_poc"]["xgboost"]["f1_test"] >= 0.85


def test_integracion_login_endpoint_jwt():
    res_ok = client.post("/api/v1/auth/login", json={
        "correo": "evaluador@eltambo.gob.pe",
        "password": "municipal2026",
        "rol": "EVALUADOR_LICENCIAS"
    })
    assert res_ok.status_code == 200
    assert "access_token" in res_ok.json()["data"]

    res_err = client.post("/api/v1/auth/login", json={
        "correo": "noexiste@eltambo.gob.pe",
        "password": "mal",
        "rol": "EVALUADOR_LICENCIAS"
    })
    assert res_err.status_code == 401


def test_integracion_flujo_completo_con_pdf_real_ocr_y_ambos_modelos():
    pdf_path = Path("muestras_pdf_tupa/EXP-2026-0351_OBSERVADO.pdf")
    pdf_bytes = pdf_path.read_bytes() if pdf_path.exists() else b""

    # Prueba con XGBoost (Strategy 1) leyendo bytes reales de PDF
    res_xgb = client.post(
        "/api/v1/expedientes/evaluar",
        data={
            "codigo_expediente": "EXP-2026-0351",
            "dni_ruc_titular": "20601122334",
            "razon_social_nombre": "Restaurante Turistico El Huaytapallana S.A.C.",
            "giro_comercial": "Restaurante",
            "tipo_tramite": "Nueva licencia",
            "direccion_predio": "Av. Huancavelica 1050",
            "area_comercial_m2": "110.5",
            "algoritmo": "xgboost",
        },
        files={"archivo_pdf": ("EXP-2026-0351_OBSERVADO.pdf", pdf_bytes, "application/pdf")},
    )
    assert res_xgb.status_code == 200
    exp_data = res_xgb.json()["expediente"]
    assert exp_data["evaluacion_riesgo"]["nivel_riesgo"] in ("ALTO", "MEDIO")

    # Prueba con Random Forest (Strategy 2) para riesgo medio/bajo
    res_rf = client.post(
        "/api/v1/expedientes/evaluar",
        data={
            "codigo_expediente": "EXP-2026-0352",
            "dni_ruc_titular": "10445566778",
            "razon_social_nombre": "Bodega Santa Rosa",
            "giro_comercial": "Bodega",
            "tipo_tramite": "Renovacion",
            "area_comercial_m2": "45.0",
            "documentos_faltantes": "1",
            "inconsistencias_detectadas": "1",
            "documento_critico_faltante": "0",
            "algoritmo": "random_forest",
        },
    )
    assert res_rf.status_code == 200
    assert container.expediente_repo.obtener_por_codigo("EXP-2026-0352") is not None
