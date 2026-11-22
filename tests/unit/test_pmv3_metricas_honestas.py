from src.adapters.outbound.ml.xgboost_strategy_adapter import (
    EntrenadorModelosPMV1,
    XGBoostStrategyAdapter,
)
from src.adapters.outbound.agents.langgraph_multiagent_adapter import (
    LangGraphStateGraphMultiagenteAdapter,
)
from src.application.use_cases.orquestar_predictamen_pmv3_uc import (
    MECANISMO_PERSISTENCIA_PREDICTAMEN,
)


def test_xgboost_importancias_son_reales_globales_y_no_constantes():
    entrenador = EntrenadorModelosPMV1()
    adaptador = XGBoostStrategyAdapter(entrenador)
    resultado = adaptador.predecir_riesgo(
        giro_comercial="Restaurante",
        tipo_tramite="Nueva licencia",
        documentos_faltantes=0,
        inconsistencias_detectadas=0,
        documento_critico_faltante=0,
    )

    esperadas = {
        columna: round(float(valor), 4)
        for columna, valor in zip(
            entrenador.COLUMNAS_X, entrenador.modelo_xgb.feature_importances_
        )
    }
    assert resultado.importancia_variables == esperadas
    assert round(sum(resultado.importancia_variables.values()), 4) == 1.0
    assert resultado.tipo_importancia == "global_feature_importance_xgboost"
    assert "global" in resultado.tipo_importancia


def test_grafo_no_simula_alucinaciones_ni_llm():
    adaptador = LangGraphStateGraphMultiagenteAdapter()
    contexto = {
        "codigo_expediente": "EXP-TEST-METRICAS",
        "giro_comercial": "Bodega",
        "zona_urbana": "CZ",
        "area_comercial_m2": 40.0,
        "documentos_faltantes": 0,
        "inconsistencias_detectadas": 0,
        "documento_critico_faltante": 0,
        "probabilidad_riesgo_ml": 0.1,
        "nivel_riesgo_ml": "BAJO",
        "similitud_coseno_rag": 0.96,
        "context_precision_rag": 0.96,
        "compatibilidad_zonificacion": "COMPATIBLE",
        "total_discrepancias_interfojas": 0,
        "alertas_interfojas": [],
        "dias_habiles_transcurridos": 2,
    }
    salida = adaptador.ejecutar_grafo_ciclico_predictamen(contexto)

    assert salida["motor_tipo"] == "determinista_sin_llm"
    assert salida["alucinaciones_detectadas_no_aplica"] is True
    assert "importancia global" in salida["texto_predictamen_explicable"]
    assert "no es una explicación local" in salida["texto_predictamen_explicable"]
    assert "no utiliza un LLM generativo" in salida["texto_predictamen_explicable"]
    assert "context_precision heurística" in salida["texto_predictamen_explicable"]


def test_mecanismo_persistencia_es_el_real():
    assert MECANISMO_PERSISTENCIA_PREDICTAMEN == "upsert_rest_predictamenes_pmv3"
