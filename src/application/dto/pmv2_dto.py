from dataclasses import dataclass
from typing import Optional


@dataclass
class IndexarNormativaInputDTO:
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
    id_fragmento: Optional[str] = None


@dataclass
class AuditarExpedientePMV2InputDTO:
    codigo_expediente: str
    giro_comercial: str
    zona_urbana: str
    dni_ruc_formulario: str
    dni_ruc_plano_dni: str
    area_formulario_m2: float
    area_plano_m2: float
    direccion_formulario: str
    direccion_plano: str


@dataclass
class GenerarLoteMasivoInputDTO:
    cantidad_transacciones: int = 600
