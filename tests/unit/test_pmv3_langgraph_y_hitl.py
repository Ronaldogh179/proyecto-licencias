import pymupdf
import pytest

from src.adapters.outbound.agents.langgraph_multiagent_adapter import (
    LangGraphStateGraphMultiagenteAdapter,
)
from src.adapters.outbound.pdf.pymupdf_acta_generator_adapter import (
    PyMuPDFActaResolutivaAdapter,
)
from src.adapters.outbound.persistence.supabase_repository_adapter import (
    HybridSupabaseExpedienteRepository,
)
from src.adapters.outbound.rag.pgvector_rag_adapter import PgVectorRAGAdapter
from src.application.dto.expediente_dto import ResultadoPrediccionDTO
from src.application.dto.pmv3_dto import (
    OrquestarPreDictamenPMV3InputDTO,
    ResolverDecisionHITLInputDTO,
)
from src.application.use_cases.orquestar_predictamen_pmv3_uc import (
    OrquestarPreDictamenMultiagentePMV3UseCase,
    ResolverDecisionHITLUseCase,
)
from src.domain.entities.orquestacion_pmv3 import (
    PreDictamenMultiagentePMV3Domain,
    TrazaNodoAgenteDomain,
)


class _PredictorFake:
    def predecir_riesgo(
        self,
        giro_comercial,
        tipo_tramite,
        documentos_faltantes,
        inconsistencias_detectadas,
        documento_critico_faltante,
    ):
        probabilidad = min(
            0.99,
            0.05
            + documentos_faltantes * 0.18
            + inconsistencias_detectadas * 0.12
            + documento_critico_faltante * 0.35,
        )
        return ResultadoPrediccionDTO(
            probabilidad_observacion=probabilidad,
            nombre_algoritmo="FakeXGBoost",
            importancia_variables={"documento_critico_faltante": 0.5},
            latencia_ms=0.5,
        )


def _contexto_base() -> dict:
    return {
        "codigo_expediente": "EXP-2026-PMV3-UNIT",
        "razon_social_nombre": "Administrado MYPE El Tambo S.A.C.",
        "giro_comercial": "Bodega",
        "zona_urbana": "CZ",
        "area_comercial_m2": 42.0,
        "area_plano_m2": 42.0,
        "area_maxima_m2": 60.0,
        "documentos_faltantes": 0,
        "inconsistencias_detectadas": 0,
        "documento_critico_faltante": 0,
        "probabilidad_riesgo_ml": 0.10,
        "nivel_riesgo_ml": "BAJO",
        "importancia_variables": {"documento_critico_faltante": 0.5},
        "similitud_coseno_rag": 0.96,
        "context_precision_rag": 0.96,
        "compatibilidad_zonificacion": "COMPATIBLE",
        "excede_area": False,
        "norma_origen": "Ordenanza Municipal N.° 018-2024-MDT/CM",
        "articulo_inciso": "Artículo 12.º, inciso c)",
        "codigo_ciiu": "4711",
        "texto_normativo_recuperado": "Texto normativo de prueba.",
        "es_conforme_interfojas": True,
        "total_discrepancias_interfojas": 0,
        "alertas_interfojas": [],
        "dias_habiles_transcurridos": 2,
        "umbral_similitud": 0.90,
    }


def _predictamen_base() -> PreDictamenMultiagentePMV3Domain:
    return PreDictamenMultiagentePMV3Domain(
        id_predictamen="PRED-PMV3-UNIT",
        id_expediente="EXP-2026-PMV3-UNIT",
        codigo_expediente="EXP-2026-PMV3-UNIT",
        razon_social_nombre="Administrado MYPE El Tambo S.A.C.",
        giro_comercial="Bodega",
        zona_urbana="CZ",
        area_comercial_m2=42.0,
        probabilidad_riesgo_ml=0.10,
        nivel_riesgo_ml="BAJO",
        similitud_coseno_rag=0.96,
        context_precision_rag=0.96,
        compatibilidad_zonificacion="COMPATIBLE",
        es_conforme_interfojas=True,
        total_discrepancias_interfojas=0,
        temperatura_llm=0.1,
        iteraciones_grafo=1,
        alucinaciones_detectadas=0,
        recomendacion_ia="OTORGAR_LICENCIA_CONFORME",
        cita_legal_consolidada="Ley N.° 28976; Ley N.° 31814; Ley N.° 29733.",
        texto_predictamen_explicable="Pre-dictamen de prueba.",
        nodos_ejecutados=[
            TrazaNodoAgenteDomain(1, "AgentePercepcionOCR", "COMPLETADO", "OK", 1.0)
        ],
        dias_habiles_transcurridos=2,
        dias_restantes_sla=6,
        estado_semaforo_sla="DENTRO_DEL_PLAZO_LEGAL",
        cumple_sla_legal=True,
        fecha_generacion_ia="2026-10-29T12:00:00+00:00",
        latencia_total_grafo_ms=4.0,
    )


def test_pmv3_hu09_grafo_ciclico_conforme_y_observado():
    adaptador = LangGraphStateGraphMultiagenteAdapter()

    conforme = adaptador.ejecutar_grafo_ciclico_predictamen(_contexto_base())
    assert conforme["iteraciones_grafo"] == 1
    assert len(conforme["nodos_ejecutados"]) == 4
    assert conforme["temperatura_llm"] == 0.1
    assert conforme["alucinaciones_detectadas"] == 0
    assert conforme["recomendacion_ia"] == "OTORGAR_LICENCIA_CONFORME"
    assert "28976" in conforme["cita_legal_consolidada"]
    assert "31814" in conforme["cita_legal_consolidada"]
    assert "29733" in conforme["cita_legal_consolidada"]
    assert "I. VISTOS" in conforme["texto_predictamen_explicable"]
    assert "V. CONTROL SLA" in conforme["texto_predictamen_explicable"]
    assert "LEY 31814" in conforme["texto_predictamen_explicable"]

    contexto_observado = _contexto_base()
    contexto_observado.update(
        {
            "documentos_faltantes": 2,
            "inconsistencias_detectadas": 2,
            "documento_critico_faltante": 1,
            "probabilidad_riesgo_ml": 0.94,
            "nivel_riesgo_ml": "ALTO",
            "similitud_coseno_rag": 0.80,
            "context_precision_rag": 0.80,
            "compatibilidad_zonificacion": "COMPATIBLE_CON_RESTRICCION",
            "excede_area": True,
            "es_conforme_interfojas": False,
            "total_discrepancias_interfojas": 2,
            "alertas_interfojas": ["Discrepancia de titularidad.", "Discordancia de metraje."],
        }
    )
    observado = adaptador.ejecutar_grafo_ciclico_predictamen(contexto_observado)
    assert observado["iteraciones_grafo"] == 2
    assert len(observado["nodos_ejecutados"]) == 6
    assert any(
        nodo.estado_nodo == "REFINAMIENTO_CICLICO"
        for nodo in observado["nodos_ejecutados"]
    )
    assert observado["recomendacion_ia"] == "EMITIR_ESQUELA_DE_OBSERVACION"


def test_pmv3_hu10_validacion_dominio_decision_hitl():
    predictamen = _predictamen_base()
    predictamen.aplicar_decision_humana_hitl(
        decision="APROBADO_HITL",
        funcionario="evaluador@eltambo.gob.pe",
        observaciones="Sustento administrativo suficiente.",
        fecha_iso="2026-10-29T13:00:00+00:00",
    )
    assert predictamen.decision_final_humano == "APROBADO_HITL"
    assert predictamen.funcionario_evaluador_firma == "evaluador@eltambo.gob.pe"
    assert predictamen.fecha_resolucion_hitl == "2026-10-29T13:00:00+00:00"

    with pytest.raises(ValueError, match="HITL debe ser"):
        predictamen.aplicar_decision_humana_hitl(
            "INVALIDO", "evaluador@eltambo.gob.pe", "Sustento válido", "2026-10-29"
        )
    with pytest.raises(ValueError, match="funcionario"):
        predictamen.aplicar_decision_humana_hitl(
            "APROBADO_HITL", "   ", "Sustento válido", "2026-10-29"
        )
    with pytest.raises(ValueError, match="5 caracteres"):
        predictamen.aplicar_decision_humana_hitl(
            "OBSERVADO_HITL", "evaluador@eltambo.gob.pe", "abc", "2026-10-29"
        )


def test_pmv3_hu10_generacion_acta_pdf_real_con_cita_legal_y_firma():
    predictamen = _predictamen_base()
    predictamen.aplicar_decision_humana_hitl(
        decision="APROBADO_HITL",
        funcionario="evaluador@eltambo.gob.pe",
        observaciones="Se aprueba la licencia conforme al pre-dictamen multiagente.",
        fecha_iso="2026-10-29T13:00:00+00:00",
    )

    pdf_bytes = PyMuPDFActaResolutivaAdapter().generar_acta_resolutiva_pdf_bytes(
        predictamen
    )
    assert pdf_bytes.startswith(b"%PDF-")

    documento = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    texto = "\n".join(pagina.get_text("text") for pagina in documento)
    documento.close()

    assert "EXP-2026-PMV3-UNIT" in texto
    assert "28976" in texto
    assert "31814" in texto
    assert "evaluador@eltambo.gob.pe" in texto
    assert "APROBADO_HITL" in texto


def test_pmv3_repositorio_hibrido_fallback_local_y_resolucion(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "")

    repo = HybridSupabaseExpedienteRepository(
        db_path=str(tmp_path / "bd_expedientes_pmv3_test.json")
    )
    assert len(repo.listar_predictamenes_pmv3()) == 3
    assert repo.obtener_predictamen_pmv3_por_codigo("EXP-2026-0348") is not None
    assert repo.obtener_predictamen_pmv3_por_codigo("EXP-2026-9999") is None

    predictamen = _predictamen_base()
    guardado = repo.guardar_predictamen_pmv3(predictamen)
    assert guardado["codigo_expediente"] == "EXP-2026-PMV3-UNIT"
    assert repo.obtener_predictamen_pmv3_por_codigo("EXP-2026-PMV3-UNIT") is predictamen

    resolucion = repo.registrar_resolucion_hitl_pmv3(
        codigo_expediente="EXP-2026-PMV3-UNIT",
        decision="OBSERVADO_HITL",
        funcionario="evaluador@eltambo.gob.pe",
        observaciones="Se notifica esquela de subsanación.",
        fecha_iso="2026-10-29T13:30:00+00:00",
    )
    assert resolucion["status"] == "ok"
    assert resolucion["fuente"] == "cache_local"
    assert predictamen.decision_final_humano == "OBSERVADO_HITL"

    metricas = repo.obtener_metricas_pmv1_pmv2()
    pmv3 = metricas["pmv3_multiagente_hitl"]
    assert pmv3["total_predictamenes_pmv3"] == 4
    assert pmv3["tasa_supervision_humana_pct"] == 100.0
    assert pmv3["alucinaciones_normativas"] == 0
    assert pmv3["latencia_promedio_grafo_ms"] >= 0.0

    carga = repo.ejecutar_carga_masiva_expedientes(500)
    assert carga["total_predictamenes_pmv3"] == 4
    assert carga["pmv3_tasa_cumplimiento_sla_pct"] == 100.0


def test_pmv3_casos_de_uso_orquestar_resolver_y_exportar(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "")

    repo = HybridSupabaseExpedienteRepository(
        db_path=str(tmp_path / "bd_expedientes_pmv3_uc_test.json")
    )
    orquestador = LangGraphStateGraphMultiagenteAdapter()
    generador_pdf = PyMuPDFActaResolutivaAdapter()

    orquestar_uc = OrquestarPreDictamenMultiagentePMV3UseCase(
        predictor_riesgo=_PredictorFake(),
        motor_rag=PgVectorRAGAdapter(),
        orquestador_grafo=orquestador,
        repositorio_pmv3=repo,
        repositorio_expedientes=repo,
    )
    resolver_uc = ResolverDecisionHITLUseCase(
        repositorio_pmv3=repo,
        generador_pdf=generador_pdf,
        repositorio_expedientes=repo,
    )

    resultado = orquestar_uc.ejecutar(
        OrquestarPreDictamenPMV3InputDTO(
            codigo_expediente="EXP-2026-PMV3-UC-001",
            giro_comercial="Restaurante",
            zona_urbana="RDM",
            area_declarada_tupa_m2=110.5,
            area_plano_arquitectura_m2=82.0,
            documentos_faltantes=2,
            inconsistencias_detectadas=1,
            documento_critico_faltante=1,
            dias_habiles_transcurridos=2,
        )
    )
    assert resultado["codigo_expediente"] == "EXP-2026-PMV3-UC-001"
    assert resultado["iteraciones_grafo"] == 2
    assert resultado["procedimiento_almacenado"] == "upsert_rest_predictamenes_pmv3"
    assert resultado["mecanismo_persistencia"] == "upsert_rest_predictamenes_pmv3"
    assert resultado["alucinaciones_detectadas"] == 0
    assert resultado["alucinaciones_detectadas_no_aplica"] is True
    assert resultado["motor_tipo"] == "determinista_sin_llm"
    assert (
        resultado["context_precision_rag_tipo"]
        == "heuristica_experimental_derivada_de_similitud_coseno"
    )
    assert repo.obtener_predictamen_pmv3_por_codigo("EXP-2026-PMV3-UC-001") is not None

    resolucion = resolver_uc.ejecutar_resolucion(
        ResolverDecisionHITLInputDTO(
            codigo_expediente="EXP-2026-PMV3-UC-001",
            decision_final_humano="OBSERVADO_HITL",
            funcionario_evaluador="evaluador@eltambo.gob.pe",
            observaciones_funcionario="Se dispone la notificación de subsanación.",
        )
    )
    assert resolucion["decision_final_humano"] == "OBSERVADO_HITL"
    assert resolucion["auditoria_inmutable"] is True
    assert resolucion["procedimiento_almacenado"] == "sp_registrar_resolucion_hitl_pmv3"

    pdf_bytes, nombre_archivo = resolver_uc.exportar_acta_pdf("EXP-2026-PMV3-UC-001")
    assert pdf_bytes.startswith(b"%PDF-")
    assert nombre_archivo == "ACTA_SIMEL_EXP-2026-PMV3-UC-001.pdf"

    pdf_sintetizado, nombre_sintetizado = resolver_uc.exportar_acta_pdf(
        "EXP-2026-PMV3-UC-002"
    )
    assert pdf_sintetizado.startswith(b"%PDF-")
    assert nombre_sintetizado == "ACTA_SIMEL_EXP-2026-PMV3-UC-002.pdf"

    with pytest.raises(ValueError, match="expediente es obligatorio"):
        orquestar_uc.ejecutar(
            OrquestarPreDictamenPMV3InputDTO(
                codigo_expediente="   ",
                giro_comercial="Bodega",
                zona_urbana="CZ",
                area_declarada_tupa_m2=20.0,
            )
        )
    with pytest.raises(ValueError, match="mayor a 0"):
        orquestar_uc.ejecutar(
            OrquestarPreDictamenPMV3InputDTO(
                codigo_expediente="EXP-2026-PMV3-UC-003",
                giro_comercial="Bodega",
                zona_urbana="CZ",
                area_declarada_tupa_m2=0.0,
            )
        )
