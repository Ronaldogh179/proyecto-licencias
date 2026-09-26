from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from src.domain.value_objects.nivel_riesgo import NivelRiesgoEnum

@dataclass
class EvaluacionRiesgoDomain:
    algoritmo_empleado: str
    resultado_observacion: int
    probabilidad_riesgo: float
    nivel_riesgo: str
    importancia_variables: Dict[str, float]
    latencia_inferencia_ms: float

@dataclass
class Expediente:
    id_expediente: str
    codigo_expediente: str
    dni_ruc_titular: str
    razon_social_nombre: str
    giro_comercial: str
    tipo_tramite: str
    direccion_predio: str
    area_comercial_m2: float
    nombre_archivo_pdf: str
    documentos_faltantes: int = 0
    inconsistencias_detectadas: int = 0
    documento_critico_faltante: int = 0
    texto_extraido_resumen: str = ""
    confianza_ocr: float = 0.0
    tiempo_ocr_seg: float = 0.0
    estado_tramite: str = "INGRESADO"
    dias_habiles_transcurridos: int = 1
    plazo_maximo_sla_dias: int = 8
    evaluacion_riesgo: Optional[EvaluacionRiesgoDomain] = None
    fecha_ingreso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def aplicar_extraccion_ocr(
        self,
        faltantes: int,
        inconsistencias: int,
        critico: int,
        texto_resumen: str,
        confianza: float,
        tiempo_seg: float,
    ) -> None:
        if not (0 <= faltantes <= 3):
            raise ValueError("documentos_faltantes debe estar entre 0 y 3.")
        if not (0 <= inconsistencias <= 3):
            raise ValueError("inconsistencias_detectadas debe estar entre 0 y 3.")
        if critico not in (0, 1):
            raise ValueError("documento_critico_faltante debe ser 0 o 1.")

        self.documentos_faltantes = faltantes
        self.inconsistencias_detectadas = inconsistencias
        self.documento_critico_faltante = critico
        self.texto_extraido_resumen = texto_resumen
        self.confianza_ocr = round(confianza, 2)
        self.tiempo_ocr_seg = round(tiempo_seg, 3)
        self.estado_tramite = "EXTRAIDO_OCR"

    def asignar_prediccion_riesgo(
        self,
        probabilidad: float,
        algoritmo: str,
        importancia: Dict[str, float],
        latencia_ms: float,
    ) -> None:
        if not (0.0 <= probabilidad <= 1.0):
            raise ValueError("La probabilidad de riesgo debe estar entre 0.0 y 1.0.")

        resultado_binario = 1 if probabilidad >= 0.50 else 0
        if probabilidad >= 0.70:
            nivel = NivelRiesgoEnum.ALTO.value
        elif probabilidad >= 0.40:
            nivel = NivelRiesgoEnum.MEDIO.value
        else:
            nivel = NivelRiesgoEnum.BAJO.value

        self.evaluacion_riesgo = EvaluacionRiesgoDomain(
            algoritmo_empleado=algoritmo,
            resultado_observacion=resultado_binario,
            probabilidad_riesgo=round(probabilidad, 4),
            nivel_riesgo=nivel,
            importancia_variables=importancia,
            latencia_inferencia_ms=round(latencia_ms, 2),
        )
        self.estado_tramite = (
            "OBSERVABLE_PRIORITARIO" if resultado_binario == 1 else "PRE_CONFORME"
        )

    def cumple_sla_legal(self) -> bool:
        return self.dias_habiles_transcurridos <= self.plazo_maximo_sla_dias
