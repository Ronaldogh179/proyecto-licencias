from src.adapters.outbound.persistence.supabase_repository_adapter import (
    HybridSupabaseExpedienteRepository,
)
from src.domain.entities.normativa_rag import (
    DictamenAuditoriaPMV2Domain,
    FragmentoNormativoDomain,
    ResultadoCruceInterFojasDomain,
)


def test_repositorio_hibrido_fallback_local_completo(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "")

    repo = HybridSupabaseExpedienteRepository(
        db_path=str(tmp_path / "bd_expedientes_test.json")
    )

    priorizados = repo.listar_todos_priorizados()
    assert len(priorizados) == 3
    assert repo.obtener_por_codigo("EXP-2026-0348") is not None
    assert repo.obtener_por_codigo("EXP-2026-9999") is None

    fragmento = FragmentoNormativoDomain(
        id_fragmento="FRAG-FALLBACK-5610-RDM",
        norma_origen="Ordenanza Municipal N.° 018-2024-MDT/CM",
        articulo_inciso="Artículo 12.º, inciso c)",
        codigo_ciiu="5610",
        giro_comercial="Restaurante",
        zona_urbana="RDM",
        compatibilidad="COMPATIBLE_CON_RESTRICCION",
        area_maxima_m2=80.0,
        texto_fragmento_chunk="Fragmento normativo de respaldo local.",
        tokens_chunk=500,
        overlap_tokens=50,
        similitud_coseno=0.93,
    )
    vector_16d = [0.25] * 16

    assert repo.guardar_fragmento_normativo(fragmento, vector_16d) is fragmento
    assert repo.listar_fragmentos_normativos() == [fragmento]

    validacion = repo.validar_zonificacion_rag_coseno("Restaurante", "RDM", 70.0)
    assert validacion["status"] == "ok"
    assert validacion["fuente"] == "cache_local"
    assert validacion["id_fragmento"] == "FRAG-FALLBACK-5610-RDM"
    assert validacion["compatibilidad"] == "COMPATIBLE_CON_RESTRICCION"
    assert validacion["excede_area"] is False
    assert validacion["compatible"] is True

    sin_coincidencia = repo.validar_zonificacion_rag_coseno("Oficina", "I1", 50.0)
    assert sin_coincidencia["status"] == "sin_coincidencia"
    assert sin_coincidencia["fuente"] == "cache_local"
    assert sin_coincidencia["compatible"] is False

    cruce = ResultadoCruceInterFojasDomain(
        dni_ruc_coincide=True,
        area_coincide=True,
        diferencia_area_m2=0.0,
        direccion_coincide=True,
        total_discrepancias=0,
        alertas_detectadas=[],
        es_conforme_cruce=True,
    )
    dictamen = DictamenAuditoriaPMV2Domain(
        id_dictamen="DICT-FALLBACK-001",
        codigo_expediente="EXP-2026-9998",
        giro_comercial="Restaurante",
        zona_urbana="RDM",
        similitud_coseno_rag=0.93,
        context_precision=0.94,
        compatibilidad_zonificacion="COMPATIBLE_CON_RESTRICCION",
        cita_legal_exacta="Ordenanza Municipal N.° 018-2024-MDT/CM, Artículo 12.º",
        texto_normativo_recuperado="Texto normativo de respaldo local.",
        resultado_cruce=cruce,
        estado_auditoria_pmv2="CONFORME_PMV2",
        pre_dictamen_explicable="Dictamen de respaldo local.",
        latencia_rag_ms=1.25,
    )

    assert repo.guardar_auditoria_pmv2(dictamen) is dictamen
    assert repo.listar_auditorias_pmv2() == [dictamen]

    metricas = repo.obtener_metricas_pmv1_pmv2()
    assert metricas["fuente"] == "cache_local"
    assert metricas["total_expedientes_pmv1"] == 3
    assert metricas["total_auditorias_pmv2"] == 1
    assert metricas["total_fragmentos_normativos"] == 1
    assert metricas["promedio_similitud_rag"] == 0.93
    assert metricas["promedio_context_precision"] == 0.94
    assert metricas["distribucion_estado_pmv2"] == {"CONFORME_PMV2": 1}

    carga = repo.ejecutar_carga_masiva_expedientes(500)
    assert carga["cantidad_solicitada"] == 500
    assert carga["total_expedientes_persistidos"] == 3
    assert carga["total_auditorias_persistidas"] == 1
    assert carga["total_fragmentos_normativos"] == 1
    assert carga["modo_persistencia"] == "local_cache"
    assert carga["fuente"] == "cache_local"
