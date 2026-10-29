import math
import time

from src.adapters.outbound.rag.pgvector_rag_adapter import PgVectorRAGAdapter
from src.application.dto.expediente_dto import ResultadoPrediccionDTO
from src.application.dto.pmv2_dto import (
    AuditarExpedientePMV2InputDTO,
    GenerarLoteMasivoInputDTO,
    IndexarNormativaInputDTO,
)
from src.application.use_cases.auditar_expediente_pmv2_uc import (
    AuditarZonificacionYCrucePMV2UseCase,
    IndexarNormativaVectorialUseCase,
    ProcesarDataMasivaUseCase,
)
from src.domain.services.auditor_interfojas_service import AuditorInterFojasService


class _RepoMemoria:
    def __init__(self) -> None:
        self.fragmentos = []
        self.auditorias = []
        self.expedientes = []

    def guardar_fragmento_normativo(self, fragmento, vector_embedding=None):
        self.fragmentos.append(fragmento)
        return fragmento

    def listar_fragmentos_normativos(self):
        return list(self.fragmentos)

    def guardar_auditoria_pmv2(self, dictamen):
        self.auditorias.append(dictamen)
        return dictamen

    def listar_auditorias_pmv2(self):
        return list(self.auditorias)

    def validar_zonificacion_rag_coseno(self, giro_comercial, zona_urbana, area_m2):
        return {"status": "ok", "fuente": "test"}

    def registrar_auditoria_cruzada_pmv2(self, dictamen):
        return {"status": "ok", "fuente": "test", "id_dictamen": dictamen.id_dictamen}

    def obtener_metricas_pmv1_pmv2(self):
        return {"fuente": "test"}

    def ejecutar_carga_masiva_expedientes(self, cantidad):
        return {
            "cantidad_solicitada": cantidad,
            "total_expedientes_persistidos": len(self.expedientes),
            "total_auditorias_persistidas": len(self.auditorias),
        }

    def guardar_lote_expedientes(self, expedientes):
        self.expedientes.extend(expedientes)
        return len(expedientes)

    def guardar_lote_auditorias_pmv2(self, dictamenes):
        self.auditorias.extend(dictamenes)
        return len(dictamenes)


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


def test_hu08_auditor_interfojas_conforme_y_con_discrepancias():
    conforme = AuditorInterFojasService.auditar_consistencia_documental(
        dni_ruc_formulario="20609845121",
        dni_ruc_plano_dni="20609845121",
        area_formulario_m2=120.0,
        area_plano_m2=122.5,
        direccion_formulario="Av. Mariscal Castilla N.° 1420 - El Tambo",
        direccion_plano="AV. MARISCAL CASTILLA N. 1420 - EL TAMBO",
    )
    assert conforme.es_conforme_cruce is True
    assert conforme.total_discrepancias == 0
    assert conforme.diferencia_area_m2 == 2.5

    observado = AuditorInterFojasService.auditar_consistencia_documental(
        dni_ruc_formulario="20609845121",
        dni_ruc_plano_dni="10458932147",
        area_formulario_m2=120.0,
        area_plano_m2=132.5,
        direccion_formulario="Av. Mariscal Castilla N.° 1420 - El Tambo",
        direccion_plano="Jr. Arequipa N.° 890 - El Tambo",
    )
    assert observado.es_conforme_cruce is False
    assert observado.total_discrepancias == 3
    assert observado.area_coincide is False
    assert observado.dni_ruc_coincide is False
    assert observado.direccion_coincide is False
    assert len(observado.alertas_detectadas) == 3


def test_hu06_hu07_rag_vector_16_dimensiones_y_similitud_coseno():
    rag = PgVectorRAGAdapter()

    vector = rag.fragmentar_y_vectorizar_norma(
        texto="Ordenanza Municipal N.° 018-2024-MDT/CM, licencia de funcionamiento.",
        giro="Restaurante",
        zona="RDM",
    )
    assert len(vector) == 16
    assert abs(math.sqrt(sum(valor * valor for valor in vector)) - 1.0) < 1e-6

    for giro in rag.GIROS:
        for zona in rag.ZONAS:
            fragmento = rag.buscar_similitud_coseno(giro, zona, 50.0)
            assert fragmento.giro_comercial == giro
            assert fragmento.zona_urbana == zona
            assert fragmento.similitud_coseno >= 0.88

    inicio = time.perf_counter()
    for _ in range(50):
        rag.buscar_similitud_coseno("Restaurante", "RDM", 120.0)
    promedio_ms = ((time.perf_counter() - inicio) * 1000.0) / 50
    assert promedio_ms < 5.0


def test_hu06_indexar_normativa_y_hu07_hu08_auditoria_zonificacion_observada():
    rag = PgVectorRAGAdapter()
    repo = _RepoMemoria()

    indexador = IndexarNormativaVectorialUseCase(rag_port=rag, repository_port=repo)
    fragmento = indexador.ejecutar(
        IndexarNormativaInputDTO(
            norma_origen="Ordenanza Municipal N.° 018-2024-MDT/CM",
            articulo_inciso="Artículo 12.º, inciso c)",
            codigo_ciiu="5610",
            giro_comercial="Restaurante",
            zona_urbana="RDM",
            compatibilidad="COMPATIBLE_CON_RESTRICCION",
            area_maxima_m2=80.0,
            texto_fragmento_chunk="Texto normativo de prueba para zonificación RDM.",
        )
    )
    assert fragmento.id_fragmento
    assert len(repo.fragmentos) == 1

    auditor = AuditarZonificacionYCrucePMV2UseCase(rag_port=rag, repository_port=repo)
    dictamen = auditor.ejecutar(
        AuditarExpedientePMV2InputDTO(
            codigo_expediente="EXP-2026-2000",
            giro_comercial="Restaurante",
            zona_urbana="RDM",
            dni_ruc_formulario="20609845121",
            dni_ruc_plano_dni="20609845121",
            area_formulario_m2=120.0,
            area_plano_m2=120.0,
            direccion_formulario="Av. Mariscal Castilla N.° 1420 - El Tambo",
            direccion_plano="Av. Mariscal Castilla N.° 1420 - El Tambo",
        )
    )
    assert dictamen.estado_auditoria_pmv2 == "OBSERVADO_POR_ZONIFICACION"
    assert dictamen.similitud_coseno_rag >= 0.85
    assert dictamen.context_precision >= 0.94
    assert "018-2024-MDT/CM" in dictamen.cita_legal_exacta
    assert "28976" in dictamen.cita_legal_exacta
    assert len(repo.auditorias) == 1


def test_data_masiva_500_expedientes_metricas_pmv1_y_pmv2():
    rag = PgVectorRAGAdapter()
    repo = _RepoMemoria()
    auditor = AuditarZonificacionYCrucePMV2UseCase(rag_port=rag, repository_port=repo)
    use_case = ProcesarDataMasivaUseCase(
        repository_port=repo,
        predictor_port=_PredictorFake(),
        rag_port=rag,
        auditoria_use_case=auditor,
    )

    metricas = use_case.ejecutar(GenerarLoteMasivoInputDTO(cantidad_transacciones=500))

    assert metricas["total_transacciones"] == 500
    assert metricas["throughput_expedientes_seg"] > 0
    assert sum(metricas["distribucion_riesgo"].values()) == 500
    assert sum(metricas["distribucion_estado_pmv2"].values()) == 500
    assert metricas["promedio_similitud_coseno"] >= 0.88
    assert metricas["promedio_context_precision"] >= 0.94
    assert len(repo.expedientes) == 500
    assert len(repo.auditorias) == 500
    assert metricas["persistencia"]["total_expedientes_persistidos"] == 500
