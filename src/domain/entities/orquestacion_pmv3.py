"""Entidades de dominio del PMV 3.

Patrón de Diseño: Domain Model + Value Object (dataclasses puras, sin frameworks).
Historias de Usuario: PMV3-1-HU09 (orquestación multiagente) y PMV3-2-HU10
(supervisión human-in-the-loop y acta resolutiva).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TrazaNodoAgenteDomain:
    """Traza auditable de la ejecución de un nodo del grafo multiagente."""

    orden_ejecucion: int
    nombre_agente: str
    estado_nodo: str
    hallazgo_principal: str
    latencia_nodo_ms: float


@dataclass
class PreDictamenMultiagentePMV3Domain:
    """Pre-dictamen técnico explicable generado por el StateGraph multiagente."""

    id_predictamen: str
    id_expediente: str
    codigo_expediente: str
    razon_social_nombre: str
    giro_comercial: str
    zona_urbana: str
    area_comercial_m2: float
    probabilidad_riesgo_ml: float
    nivel_riesgo_ml: str
    similitud_coseno_rag: float
    context_precision_rag: float
    compatibilidad_zonificacion: str
    es_conforme_interfojas: bool
    total_discrepancias_interfojas: int
    temperatura_llm: float
    iteraciones_grafo: int
    alucinaciones_detectadas: int
    recomendacion_ia: str
    cita_legal_consolidada: str
    texto_predictamen_explicable: str
    nodos_ejecutados: List[TrazaNodoAgenteDomain]
    dias_habiles_transcurridos: int
    dias_restantes_sla: int
    estado_semaforo_sla: str
    cumple_sla_legal: bool
    decision_final_humano: str = "PENDIENTE_REVISION_HITL"
    funcionario_evaluador_firma: str = ""
    observaciones_funcionario_hitl: str = ""
    fecha_generacion_ia: str = ""
    fecha_resolucion_hitl: Optional[str] = None
    latencia_total_grafo_ms: float = 0.0
    tipo_importancia_xai: str = "global_feature_importance_xgboost"
    context_precision_rag_tipo: str = (
        "heuristica_experimental_derivada_de_similitud_coseno"
    )
    motor_tipo: str = "determinista_sin_llm"
    alucinaciones_detectadas_no_aplica: bool = True

    def aplicar_decision_humana_hitl(
        self,
        decision: str,
        funcionario: str,
        observaciones: str,
        fecha_iso: str,
    ) -> None:
        """Registra la decisión administrativa obligatoria del funcionario.

        Patrón: Human-in-the-Loop (Ley N.° 31814). La IA solo recomienda; la
        decisión final y la firma siempre pertenecen a una persona.
        """

        decisiones_validas = ("APROBADO_HITL", "OBSERVADO_HITL", "RECHAZADO_HITL")
        if decision not in decisiones_validas:
            raise ValueError(
                "La decisión HITL debe ser APROBADO_HITL, OBSERVADO_HITL o RECHAZADO_HITL."
            )
        if not funcionario or not funcionario.strip():
            raise ValueError("El funcionario evaluador firmante es obligatorio.")
        if not observaciones or len(observaciones.strip()) < 5:
            raise ValueError("El sustento administrativo debe tener al menos 5 caracteres.")

        self.decision_final_humano = decision
        self.funcionario_evaluador_firma = funcionario.strip()
        self.observaciones_funcionario_hitl = observaciones.strip()
        self.fecha_resolucion_hitl = fecha_iso
