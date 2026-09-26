from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class IngresoExpedienteInputDTO:
    codigo_expediente: str
    dni_ruc_titular: str
    razon_social_nombre: str
    giro_comercial: str
    tipo_tramite: str
    direccion_predio: str
    area_comercial_m2: float
    nombre_archivo_pdf: str
    contenido_pdf_bytes: bytes
    documentos_faltantes_manual: Optional[int] = None
    inconsistencias_manual: Optional[int] = None
    documento_critico_manual: Optional[int] = None
    algoritmo_preferido: str = "xgboost"

@dataclass
class ResultadoOCRDTO:
    documentos_faltantes: int
    inconsistencias_detectadas: int
    documento_critico_faltante: int
    texto_resumen: str
    confianza_ocr: float
    tiempo_seg: float

@dataclass
class ResultadoPrediccionDTO:
    probabilidad_observacion: float
    nombre_algoritmo: str
    importancia_variables: Dict[str, float]
    latencia_ms: float
