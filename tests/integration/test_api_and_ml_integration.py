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


def test_pmv2_endpoints_rag_y_cruce_interfojas():
    res_index = client.post(
        "/api/v1/rag/indexar-normativa",
        json={
            "id_fragmento": "FRAG-HU06-INTEGRATION-5610-RDM",
            "norma_origen": "Ordenanza Municipal N.° 018-2024-MDT/CM",
            "articulo_inciso": "Artículo 12.º, inciso c) - Cuadro de Índice de Usos",
            "codigo_ciiu": "5610",
            "giro_comercial": "Restaurante",
            "zona_urbana": "RDM",
            "compatibilidad": "COMPATIBLE_CON_RESTRICCION",
            "area_maxima_m2": 80.0,
            "texto_fragmento_chunk": (
                "Ordenanza Municipal N.° 018-2024-MDT/CM. Fragmento de integración "
                "para validar chunking 500/50 y persistencia vectorial pgvector."
            ),
            "tokens_chunk": 500,
            "overlap_tokens": 50,
        },
    )
    assert res_index.status_code == 200
    body_index = res_index.json()
    assert body_index["status"] == "ok"
    assert body_index["fragmento"]["id_fragmento"] == "FRAG-HU06-INTEGRATION-5610-RDM"
    assert body_index["fragmento"]["codigo_ciiu"] == "5610"
    assert body_index["fragmento"]["tokens_chunk"] == 500
    assert body_index["fragmento"]["overlap_tokens"] == 50
    assert body_index["dimensiones_vector"] == 16
    assert len(body_index["vector_embedding"]) == 16
    assert body_index["procedimiento_almacenado"] == "sp_indexar_fragmento_normativo"

    res_audit = client.post(
        "/api/v1/rag/auditar-expediente",
        json={
            "codigo_expediente": "EXP-2026-HU08-INTEGRATION",
            "giro_comercial": "Restaurante",
            "zona_urbana": "RDM",
            "dni_ruc_formulario": "20601122334",
            "dni_ruc_plano_dni": "10728491023",
            "area_formulario_m2": 110.50,
            "area_plano_m2": 82.00,
            "direccion_formulario": "Av. Huancavelica N.° 1050 - El Tambo",
            "direccion_plano": "Av. Huancavelica N.° 1050 - El Tambo",
        },
    )
    assert res_audit.status_code == 200
    body_audit = res_audit.json()
    assert body_audit["status"] == "ok"
    assert body_audit["procedimiento_almacenado"] == "sp_registrar_auditoria_cruzada_pmv2"

    auditoria = body_audit["auditoria"]
    claves_requeridas = {
        "id_dictamen",
        "codigo_expediente",
        "giro_comercial",
        "zona_urbana",
        "similitud_coseno_rag",
        "context_precision",
        "compatibilidad_zonificacion",
        "cita_legal_exacta",
        "texto_normativo_recuperado",
        "resultado_cruce_interfojas",
        "estado_auditoria_pmv2",
        "pre_dictamen_explicable",
        "latencia_rag_ms",
    }
    assert claves_requeridas.issubset(auditoria.keys())
    assert auditoria["codigo_expediente"] == "EXP-2026-HU08-INTEGRATION"
    assert auditoria["similitud_coseno_rag"] >= 0.85
    assert auditoria["context_precision"] >= 0.94
    assert auditoria["estado_auditoria_pmv2"] == "OBSERVADO_INTERFOJAS_O_ZONIFICACION"
    assert auditoria["resultado_cruce_interfojas"]["diferencia_area_m2"] == 28.5
    assert auditoria["resultado_cruce_interfojas"]["dni_ruc_coincide"] is False
    assert auditoria["resultado_cruce_interfojas"]["area_coincide"] is False
    assert auditoria["resultado_cruce_interfojas"]["direccion_coincide"] is True


def test_pmv2_carga_masiva_500_transacciones_y_metricas():
    res_masiva = client.post(
        "/api/v1/expedientes/carga-masiva",
        json={"cantidad": 500},
    )
    assert res_masiva.status_code == 200
    body_masiva = res_masiva.json()
    assert body_masiva["status"] == "ok"
    assert body_masiva["total_procesados"] == 500
    assert body_masiva["throughput_exp_seg"] > 0
    assert (
        body_masiva["riesgo_alto"]
        + body_masiva["riesgo_medio"]
        + body_masiva["riesgo_bajo"]
        == 500
    )
    assert (
        body_masiva["compatibles"]
        + body_masiva["condicionados"]
        + body_masiva["incompatibles"]
        == 500
    )
    assert body_masiva["promedio_similitud_coseno"] >= 0.85
    assert body_masiva["promedio_context_precision"] >= 0.94
    assert body_masiva["persistencia"]["cantidad_solicitada"] == 500
    assert body_masiva["persistencia"]["total_expedientes_persistidos"] >= 500
    assert body_masiva["persistencia"]["total_auditorias_persistidas"] >= 500

    res_metricas = client.get("/api/v1/metricas/consolidado")
    assert res_metricas.status_code == 200
    body_metricas = res_metricas.json()
    assert body_metricas["status"] == "ok"
    assert body_metricas["pmv1_ml"]["f1_score"] >= 0.85
    assert body_metricas["pmv1_ml"]["recall"] >= 0.85
    assert body_metricas["pmv2_rag"]["context_precision"] >= 0.94
    assert body_metricas["pmv2_rag"]["similitud_coseno_promedio"] >= 0.85
    assert body_metricas["stored_procedures"]["total_activos"] == 4
    assert body_metricas["stored_procedures"]["fuente"] in {
        "supabase_rpc",
        "cache_local",
    }


def test_pmv2_listados_router_legacy_y_validaciones_422():
    res_normativas = client.get("/api/v1/rag/normativas")
    assert res_normativas.status_code == 200
    assert res_normativas.json()["total"] >= 20
    assert res_normativas.json()["motor_vectorial"].startswith("pgvector HNSW")

    res_auditorias = client.get("/api/v1/rag/auditorias")
    assert res_auditorias.status_code == 200
    assert res_auditorias.json()["total"] >= 1

    res_index = client.post(
        "/api/v1/pmv2/normativa/indexar",
        json={
            "id_fragmento": "FRAG-LEGACY-HU06-6910-CZ",
            "norma_origen": "Ordenanza Municipal N.° 018-2024-MDT/CM",
            "articulo_inciso": "Artículo 12.º, inciso c)",
            "codigo_ciiu": "6910",
            "giro_comercial": "Oficina",
            "zona_urbana": "CZ",
            "compatibilidad": "COMPATIBLE",
            "area_maxima_m2": 100.0,
            "texto_fragmento_chunk": "Fragmento normativo del router legacy PMV2.",
            "tokens_chunk": 500,
            "overlap_tokens": 50,
        },
    )
    assert res_index.status_code == 200
    assert res_index.json()["status"] == "created"
    assert res_index.json()["fragmento"]["id_fragmento"] == "FRAG-LEGACY-HU06-6910-CZ"

    res_audit = client.post(
        "/api/v1/pmv2/auditorias/auditar",
        json={
            "codigo_expediente": "EXP-2026-LEGACY-CONFORME",
            "giro_comercial": "Bodega",
            "zona_urbana": "CZ",
            "dni_ruc_formulario": "10728491023",
            "dni_ruc_plano_dni": "10728491023",
            "area_formulario_m2": 42.0,
            "area_plano_m2": 42.0,
            "direccion_formulario": "Jr. Arequipa N.° 890 - El Tambo",
            "direccion_plano": "Jr. Arequipa N.° 890 - El Tambo",
        },
    )
    assert res_audit.status_code == 200
    assert res_audit.json()["status"] == "ok"
    assert res_audit.json()["dictamen"]["estado_auditoria_pmv2"] == "CONFORME_PMV2"
    assert res_audit.json()["dictamen"]["compatibilidad_zonificacion"] == "COMPATIBLE"

    res_historial = client.get("/api/v1/pmv2/auditorias")
    assert res_historial.status_code == 200
    assert res_historial.json()["total"] >= 1

    res_fragmentos = client.get("/api/v1/pmv2/fragmentos")
    assert res_fragmentos.status_code == 200
    assert res_fragmentos.json()["total"] >= 1

    res_metricas = client.get("/api/v1/pmv2/metricas")
    assert res_metricas.status_code == 200
    assert res_metricas.json()["status"] == "ok"

    res_index_invalido = client.post(
        "/api/v1/rag/indexar-normativa",
        json={"texto_fragmento_chunk": "   "},
    )
    assert res_index_invalido.status_code == 422

    res_masiva_invalida = client.post(
        "/api/v1/expedientes/carga-masiva",
        json={"cantidad": 499},
    )
    assert res_masiva_invalida.status_code == 422

    res_legacy_invalida = client.post(
        "/api/v1/pmv2/data-masiva",
        json={"cantidad_transacciones": 499},
    )
    assert res_legacy_invalida.status_code == 422
