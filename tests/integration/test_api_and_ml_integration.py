from pathlib import Path
from fastapi.testclient import TestClient
from src.infrastructure.main import app
from src.infrastructure.container import container

client = TestClient(app)


def _login_pmv3(
    correo: str = "evaluador@eltambo.gob.pe",
    rol: str = "EVALUADOR_LICENCIAS",
) -> dict:
    respuesta = client.post(
        "/api/v1/auth/login",
        json={
            "correo": correo,
            "password": "municipal2026",
            "rol": rol,
        },
    )
    assert respuesta.status_code == 200
    token = respuesta.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


AUTH_HEADERS = _login_pmv3()


def test_integracion_endpoint_dashboard_y_bandeja_priorizada():
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "SIMEL" in res_html.text

    res_bandeja = client.get("/api/v1/expedientes/bandeja", headers=AUTH_HEADERS)
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
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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
    res_normativas = client.get("/api/v1/rag/normativas", headers=AUTH_HEADERS)
    assert res_normativas.status_code == 200
    assert res_normativas.json()["total"] >= 20
    assert res_normativas.json()["motor_vectorial"].startswith("pgvector HNSW")

    res_auditorias = client.get("/api/v1/rag/auditorias", headers=AUTH_HEADERS)
    assert res_auditorias.status_code == 200
    assert res_auditorias.json()["total"] >= 1

    res_index = client.post(
        "/api/v1/pmv2/normativa/indexar",
        headers=AUTH_HEADERS,
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
        headers=AUTH_HEADERS,
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

    res_historial = client.get("/api/v1/pmv2/auditorias", headers=AUTH_HEADERS)
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
        headers=AUTH_HEADERS,
        json={"texto_fragmento_chunk": "   "},
    )
    assert res_index_invalido.status_code == 422

    res_masiva_invalida = client.post(
        "/api/v1/expedientes/carga-masiva",
        headers=AUTH_HEADERS,
        json={"cantidad": 499},
    )
    assert res_masiva_invalida.status_code == 422

    res_legacy_invalida = client.post(
        "/api/v1/pmv2/data-masiva",
        headers=AUTH_HEADERS,
        json={"cantidad_transacciones": 499},
    )
    assert res_legacy_invalida.status_code == 422


def test_pmv3_endpoints_multiagente_hitl_acta_y_alias():
    payload = {
        "codigo_expediente": "EXP-2026-PMV3-INTEGRATION",
        "giro_comercial": "Restaurante",
        "zona_urbana": "RDM",
        "area_declarada_tupa_m2": 110.5,
        "area_plano_arquitectura_m2": 82.0,
        "dni_ruc_tupa": "20601122334",
        "dni_ruc_documento_identidad": "10728491023",
        "direccion_tupa": "Av. Huancavelica N. 1050 - El Tambo",
        "direccion_plano": "Av. Huancavelica N. 1050 - El Tambo",
        "documentos_faltantes": 2,
        "inconsistencias_detectadas": 1,
        "documento_critico_faltante": 1,
        "dias_habiles_transcurridos": 2,
    }
    headers = _login_pmv3()
    res_orquestar = client.post(
        "/api/v1/pmv3/predictamen/orquestar", json=payload, headers=headers
    )
    assert res_orquestar.status_code == 200
    body_orquestar = res_orquestar.json()
    assert body_orquestar["status"] == "success"
    assert body_orquestar["procedimiento_almacenado"] == "upsert_rest_predictamenes_pmv3"
    assert body_orquestar["mecanismo_persistencia"] == "upsert_rest_predictamenes_pmv3"
    predictamen = body_orquestar["predictamen"]
    assert predictamen["codigo_expediente"] == "EXP-2026-PMV3-INTEGRATION"
    assert predictamen["iteraciones_grafo"] == 2
    assert len(predictamen["nodos_ejecutados"]) == 6
    assert predictamen["temperatura_llm"] == 0.1
    assert predictamen["alucinaciones_detectadas"] == 0
    assert predictamen["decision_final_humano"] == "PENDIENTE_REVISION_HITL"
    assert predictamen["estado_semaforo_sla"] == "DENTRO_DEL_PLAZO_LEGAL"
    assert predictamen["cumple_sla_legal"] is True
    assert "28976" in predictamen["cita_legal_consolidada"]
    assert "31814" in predictamen["cita_legal_consolidada"]
    assert any(
        nodo["estado_nodo"] == "REFINAMIENTO_CICLICO"
        for nodo in predictamen["nodos_ejecutados"]
    )

    res_listar = client.get("/api/v1/pmv3/predictamenes", headers=headers)
    assert res_listar.status_code == 200
    body_listar = res_listar.json()
    assert body_listar["status"] == "success"
    assert body_listar["total"] >= 3
    codigos = [item["codigo_expediente"] for item in body_listar["predictamenes"]]
    assert "EXP-2026-PMV3-INTEGRATION" in codigos
    assert "EXP-2026-0348" in codigos

    res_hitl = client.post(
        "/api/v1/pmv3/hitl/resolver",
        json={
            "codigo_expediente": "EXP-2026-PMV3-INTEGRATION",
            "decision_final_humano": "OBSERVADO_HITL",
            "funcionario_evaluador": "evaluador@eltambo.gob.pe",
            "observaciones_funcionario": "Se notifica esquela de subsanacion documental.",
        },
        headers=headers,
    )
    assert res_hitl.status_code == 200
    body_hitl = res_hitl.json()
    assert body_hitl["status"] == "success"
    assert body_hitl["auditoria_inmutable"] is True
    assert body_hitl["procedimiento_almacenado"] == "sp_registrar_resolucion_hitl_pmv3"
    assert body_hitl["predictamen"]["decision_final_humano"] == "OBSERVADO_HITL"
    assert body_hitl["predictamen"]["funcionario_evaluador_firma"] == "evaluador@eltambo.gob.pe"

    res_pdf = client.get(
        "/api/v1/pmv3/acta-pdf/EXP-2026-PMV3-INTEGRATION", headers=headers
    )
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert "ACTA_SIMEL_EXP-2026-PMV3-INTEGRATION.pdf" in res_pdf.headers["content-disposition"]
    assert res_pdf.content.startswith(b"%PDF-")

    res_alias_orquestar = client.post(
        "/api/v1/agentes/orquestar-predictamen", json=payload, headers=headers
    )
    assert res_alias_orquestar.status_code == 200
    assert res_alias_orquestar.json()["status"] == "success"

    res_alias_listar = client.get("/api/v1/agentes/predictamenes", headers=headers)
    assert res_alias_listar.status_code == 200
    assert res_alias_listar.json()["total"] >= 3

    res_alias_hitl = client.post(
        "/api/v1/hitl/resolver-dictamen",
        json={
            "codigo_expediente": "EXP-2026-PMV3-INTEGRATION",
            "decision_final_humano": "APROBADO_HITL",
            "funcionario_evaluador": "evaluador@eltambo.gob.pe",
            "observaciones_funcionario": "Se aprueba la licencia tras verificar el pre-dictamen.",
        },
        headers=headers,
    )
    assert res_alias_hitl.status_code == 200
    assert res_alias_hitl.json()["predictamen"]["decision_final_humano"] == "APROBADO_HITL"

    res_alias_pdf = client.get(
        "/api/v1/hitl/exportar-acta/EXP-2026-PMV3-INTEGRATION", headers=headers
    )
    assert res_alias_pdf.status_code == 200
    assert res_alias_pdf.content.startswith(b"%PDF-")


def test_pmv3_metricas_consolidadas_y_validaciones_422():
    headers = _login_pmv3()
    res_metricas = client.get("/api/v1/metricas/consolidado")
    assert res_metricas.status_code == 200
    body_metricas = res_metricas.json()
    assert body_metricas["status"] == "ok"
    sp = body_metricas["stored_procedures"]
    assert sp["total_activos"] == 4
    assert sp["total_activos_pmv3"] == 1
    assert sp["total_activos_sistema"] == 5
    assert sp["sp_registrar_resolucion_hitl_pmv3"] == "ACTIVO"
    pmv3 = body_metricas["pmv3_multiagente_hitl"]
    assert pmv3["total_predictamenes_pmv3"] >= 3
    assert pmv3["tasa_supervision_humana_pct"] == 100.0
    assert pmv3["tasa_cumplimiento_sla_pct"] == 100.0
    assert pmv3["alucinaciones_normativas"] == 0
    assert pmv3["alucinaciones_normativas_tipo"] == "no_aplica_sin_llm_generativo"
    assert pmv3["temperatura_determinista"] == 0.1
    assert pmv3["motor_tipo"] == "determinista_sin_llm"
    assert (
        pmv3["context_precision_pmv3_tipo"]
        == "heuristica_experimental_derivada_de_similitud_coseno"
    )

    res_area_invalida = client.post(
        "/api/v1/pmv3/predictamen/orquestar",
        json={
            "codigo_expediente": "EXP-2026-PMV3-AREA-0",
            "giro_comercial": "Bodega",
            "zona_urbana": "CZ",
            "area_declarada_tupa_m2": 0.0,
        },
        headers=headers,
    )
    assert res_area_invalida.status_code == 422

    res_decision_invalida = client.post(
        "/api/v1/pmv3/hitl/resolver",
        json={
            "codigo_expediente": "EXP-2026-0348",
            "decision_final_humano": "DECISION_INVENTADA",
            "funcionario_evaluador": "evaluador@eltambo.gob.pe",
            "observaciones_funcionario": "Sustento administrativo suficiente.",
        },
        headers=headers,
    )
    assert res_decision_invalida.status_code == 422

    res_sustento_invalido = client.post(
        "/api/v1/pmv3/hitl/resolver",
        json={
            "codigo_expediente": "EXP-2026-0348",
            "decision_final_humano": "APROBADO_HITL",
            "funcionario_evaluador": "evaluador@eltambo.gob.pe",
            "observaciones_funcionario": "abc",
        },
        headers=headers,
    )
    assert res_sustento_invalido.status_code == 422
