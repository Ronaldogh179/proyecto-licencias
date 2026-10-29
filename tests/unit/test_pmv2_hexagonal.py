import math
from unittest.mock import MagicMock

import pytest

from src.adapters.outbound.rag.pgvector_rag_adapter import PgVectorRAGAdapter
from src.application.dto.pmv2_dto import (
    AuditarExpedientePMV2InputDTO,
    IndexarNormativaInputDTO,
)
from src.application.use_cases.auditar_expediente_pmv2_uc import (
    AuditarZonificacionYCrucePMV2UseCase,
    IndexarNormativaVectorialUseCase,
)
from src.domain.entities.normativa_rag import FragmentoNormativoDomain
from src.domain.services.auditor_interfojas_service import AuditorInterFojasService


def test_hu06_indexacion_vectorial_chunking_pgvector():
    texto_normativo = " ".join(f"clausula_normativa_{indice}" for indice in range(520))
    vector_16d = [0.25] * 16

    rag_port = MagicMock()
    rag_port.fragmentar_y_vectorizar_norma.return_value = vector_16d
    repository_port = MagicMock()
    repository_port.guardar_fragmento_normativo.side_effect = (
        lambda fragmento, vector_embedding=None: fragmento
    )

    use_case = IndexarNormativaVectorialUseCase(
        rag_port=rag_port,
        repository_port=repository_port,
    )
    dto = IndexarNormativaInputDTO(
        id_fragmento="FRAG-HU06-MOCK-5610-RDM",
        norma_origen="Ordenanza Municipal N.° 018-2024-MDT/CM",
        articulo_inciso="Artículo 12.º, inciso c)",
        codigo_ciiu="5610",
        giro_comercial="Restaurante",
        zona_urbana="RDM",
        compatibilidad="COMPATIBLE_CON_RESTRICCION",
        area_maxima_m2=80.0,
        texto_fragmento_chunk=texto_normativo,
        tokens_chunk=500,
        overlap_tokens=50,
    )

    fragmento = use_case.ejecutar(dto)

    assert isinstance(fragmento, FragmentoNormativoDomain)
    assert fragmento.id_fragmento == "FRAG-HU06-MOCK-5610-RDM"
    assert fragmento.tokens_chunk == 500
    assert fragmento.overlap_tokens == 50
    assert fragmento.codigo_ciiu == "5610"
    assert fragmento.zona_urbana == "RDM"
    assert fragmento.compatibilidad == "COMPATIBLE_CON_RESTRICCION"
    assert len(texto_normativo.split()) == 520
    assert fragmento.texto_fragmento_chunk == texto_normativo

    rag_port.fragmentar_y_vectorizar_norma.assert_called_once_with(
        texto=texto_normativo,
        giro="Restaurante",
        zona="RDM",
    )
    rag_port.indexar_fragmento.assert_called_once_with(fragmento)
    repository_port.guardar_fragmento_normativo.assert_called_once_with(
        fragmento,
        vector_16d,
    )


def test_hu07_motor_rag_similitud_coseno_zonificacion():
    vector_a = [0.6, 0.8, 0.0]
    vector_b = [0.8, 0.6, 0.0]
    similitud_formula = PgVectorRAGAdapter._similitud_coseno(vector_a, vector_b)
    assert math.isclose(similitud_formula, 0.96, rel_tol=1e-9)
    assert similitud_formula >= 0.85

    def construir_fragmento(zona_urbana: str) -> FragmentoNormativoDomain:
        es_rdm = zona_urbana == "RDM"
        return FragmentoNormativoDomain(
            id_fragmento=f"FRAG-CIIU-5610-{zona_urbana}",
            norma_origen="Ordenanza Municipal N.° 018-2024-MDT/CM",
            articulo_inciso="Artículo 12.º, inciso c) - Cuadro de Índice de Usos CIIU-5610",
            codigo_ciiu="5610",
            giro_comercial="Restaurante",
            zona_urbana=zona_urbana,
            compatibilidad=(
                "COMPATIBLE_CON_RESTRICCION" if es_rdm else "COMPATIBLE"
            ),
            area_maxima_m2=80.0 if es_rdm else 150.0,
            texto_fragmento_chunk="Texto normativo de zonificación recuperado por Mock.",
            tokens_chunk=500,
            overlap_tokens=50,
            similitud_coseno=0.93,
        )

    rag_port = MagicMock()
    rag_port.buscar_similitud_coseno.side_effect = (
        lambda giro_comercial, zona_urbana, area_m2: construir_fragmento(zona_urbana)
    )
    repository_port = MagicMock()
    repository_port.guardar_auditoria_pmv2.side_effect = lambda dictamen: dictamen

    use_case = AuditarZonificacionYCrucePMV2UseCase(
        rag_port=rag_port,
        repository_port=repository_port,
    )

    dictamen_rdm = use_case.ejecutar(
        AuditarExpedientePMV2InputDTO(
            codigo_expediente="EXP-2026-HU07-RDM",
            giro_comercial="Restaurante",
            zona_urbana="RDM",
            dni_ruc_formulario="20601122334",
            dni_ruc_plano_dni="20601122334",
            area_formulario_m2=70.0,
            area_plano_m2=70.0,
            direccion_formulario="Av. Huancavelica N.° 1050 - El Tambo",
            direccion_plano="Av. Huancavelica N.° 1050 - El Tambo",
        )
    )
    dictamen_cz = use_case.ejecutar(
        AuditarExpedientePMV2InputDTO(
            codigo_expediente="EXP-2026-HU07-CZ",
            giro_comercial="Restaurante",
            zona_urbana="CZ",
            dni_ruc_formulario="20601122334",
            dni_ruc_plano_dni="20601122334",
            area_formulario_m2=70.0,
            area_plano_m2=70.0,
            direccion_formulario="Av. Huancavelica N.° 1050 - El Tambo",
            direccion_plano="Av. Huancavelica N.° 1050 - El Tambo",
        )
    )

    assert dictamen_rdm.similitud_coseno_rag >= 0.85
    assert dictamen_rdm.context_precision >= 0.94
    assert dictamen_rdm.compatibilidad_zonificacion == "COMPATIBLE_CON_RESTRICCION"
    assert dictamen_rdm.estado_auditoria_pmv2 == "CONFORME_PMV2"
    assert "CIIU-5610" in dictamen_rdm.cita_legal_exacta
    assert "28976" in dictamen_rdm.cita_legal_exacta
    assert dictamen_cz.compatibilidad_zonificacion == "COMPATIBLE"
    assert dictamen_cz.estado_auditoria_pmv2 == "CONFORME_PMV2"
    assert rag_port.buscar_similitud_coseno.call_count == 2
    assert repository_port.guardar_auditoria_pmv2.call_count == 2


def test_hu08_auditoria_cruzada_interfojas_dominio_puro():
    resultado = AuditorInterFojasService.auditar_consistencia_documental(
        dni_ruc_formulario="20601122334",
        dni_ruc_plano_dni="10728491023",
        area_formulario_m2=110.50,
        area_plano_m2=82.00,
        direccion_formulario="Av. Huancavelica N.° 1050 - El Tambo",
        direccion_plano="AV. HUANCAVELICA N. 1050 - EL TAMBO",
    )

    assert resultado.diferencia_area_m2 == 28.5
    assert resultado.area_coincide is False
    assert resultado.dni_ruc_coincide is False
    assert resultado.direccion_coincide is True
    assert resultado.total_discrepancias == 2
    assert resultado.es_conforme_cruce is False

    alertas = " ".join(resultado.alertas_detectadas)
    assert "110.5 m²" in alertas
    assert "82.0 m²" in alertas
    assert "28.5 m²" in alertas
    assert "titularidad" in alertas
