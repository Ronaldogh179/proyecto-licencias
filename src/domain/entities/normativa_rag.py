from dataclasses import dataclass
from typing import List


@dataclass
class FragmentoNormativoDomain:
    id_fragmento: str
    norma_origen: str
    articulo_inciso: str
    codigo_ciiu: str
    giro_comercial: str
    zona_urbana: str
    compatibilidad: str
    area_maxima_m2: float
    texto_fragmento_chunk: str
    tokens_chunk: int = 500
    overlap_tokens: int = 50
    similitud_coseno: float = 0.0


@dataclass
class ResultadoCruceInterFojasDomain:
    dni_ruc_coincide: bool
    area_coincide: bool
    diferencia_area_m2: float
    direccion_coincide: bool
    total_discrepancias: int
    alertas_detectadas: List[str]
    es_conforme_cruce: bool


@dataclass
class DictamenAuditoriaPMV2Domain:
    id_dictamen: str
    codigo_expediente: str
    giro_comercial: str
    zona_urbana: str
    similitud_coseno_rag: float
    context_precision: float
    compatibilidad_zonificacion: str
    cita_legal_exacta: str
    texto_normativo_recuperado: str
    resultado_cruce: ResultadoCruceInterFojasDomain
    estado_auditoria_pmv2: str
    pre_dictamen_explicable: str
    latencia_rag_ms: float
