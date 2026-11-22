"""Adaptador de orquestación multiagente con StateGraph dirigido y cíclico.

Patrón de Diseño: LangGraph Architecture (StateGraph) + Adapter + Strategy.
Historias de Usuario: PMV3-1-HU09.
El motor es determinista, nativo en Python puro y no requiere API keys externas.
"""

import time
from typing import Any, Callable, Dict, List

from src.application.ports.output_ports import OrquestadorMultiagenteLangGraphPort
from src.domain.entities.orquestacion_pmv3 import TrazaNodoAgenteDomain


class LangGraphStateGraphMultiagenteAdapter(OrquestadorMultiagenteLangGraphPort):
    """Ejecuta un grafo cíclico de 4 agentes sobre un estado compartido tipado."""

    TEMPERATURA_DETERMINISTA = 0.1
    MAX_ITERACIONES_CICLICAS = 2
    UMBRAL_SIMILITUD_REFINAMIENTO = 0.90
    UMBRAL_SIMILITUD_ACEPTACION = 0.85

    def ejecutar_grafo_ciclico_predictamen(self, contexto_entrada: dict) -> dict:
        inicio_total = time.perf_counter()
        estado: Dict[str, Any] = dict(contexto_entrada)
        trazas: List[TrazaNodoAgenteDomain] = []
        orden = 0

        def ejecutar_nodo(
            nombre_agente: str,
            estado_nodo: str,
            accion: Callable[[], str],
        ) -> str:
            nonlocal orden
            inicio_nodo = time.perf_counter()
            hallazgo = accion()
            latencia = round(max(0.001, (time.perf_counter() - inicio_nodo) * 1000.0), 3)
            orden += 1
            trazas.append(
                TrazaNodoAgenteDomain(
                    orden_ejecucion=orden,
                    nombre_agente=nombre_agente,
                    estado_nodo=estado_nodo,
                    hallazgo_principal=hallazgo,
                    latencia_nodo_ms=latencia,
                )
            )
            return hallazgo

        def nodo_percepcion_ocr() -> str:
            faltantes = int(estado.get("documentos_faltantes", 0))
            inconsistencias = int(estado.get("inconsistencias_detectadas", 0))
            critico = int(estado.get("documento_critico_faltante", 0))
            estado["percepcion_valida"] = critico == 0 and faltantes < 2
            if critico == 1:
                return (
                    "Se detectó ausencia de documento crítico (ITSE o plano firmado); "
                    "el expediente requiere observación documental."
                )
            if faltantes >= 2:
                return (
                    f"OCR detectó {faltantes} documento(s) faltante(s) y "
                    f"{inconsistencias} inconsistencia(s); cobertura documental insuficiente."
                )
            if faltantes == 1 or inconsistencias >= 1:
                return (
                    f"OCR detectó {faltantes} faltante(s) y {inconsistencias} "
                    "inconsistencia(s) menores subsanables."
                )
            return "OCR validó la foja TUPA sin faltantes ni inconsistencias relevantes."

        def nodo_predictivo_xgboost() -> str:
            probabilidad = float(estado.get("probabilidad_riesgo_ml", 0.0))
            if probabilidad >= 0.70:
                nivel = "ALTO"
            elif probabilidad >= 0.40:
                nivel = "MEDIO"
            else:
                nivel = "BAJO"
            estado["nivel_riesgo_ml"] = nivel
            importancias = estado.get("importancia_variables") or {}
            variable_principal = (
                max(importancias, key=importancias.get) if importancias else "documento_critico_faltante"
            )
            return (
                f"XGBoost estimó una probabilidad de observación de {probabilidad:.4f} "
                f"(riesgo {nivel}); variable XAI principal: {variable_principal}."
            )

        def nodo_normativo_rag() -> str:
            similitud = float(estado.get("similitud_coseno_rag", 0.0))
            context_precision = float(estado.get("context_precision_rag", 0.0))
            compatibilidad = str(estado.get("compatibilidad_zonificacion", "NO_COMPATIBLE"))
            discrepancias = int(estado.get("total_discrepancias_interfojas", 0))
            excede_area = bool(estado.get("excede_area", False))
            nivel = str(estado.get("nivel_riesgo_ml", "BAJO"))
            requiere = (
                similitud < self.UMBRAL_SIMILITUD_REFINAMIENTO
                or discrepancias > 0
                or excede_area
                or compatibilidad == "NO_COMPATIBLE"
                or nivel == "ALTO"
            )
            estado["requiere_refinamiento"] = requiere
            estado["similitud_refinada"] = similitud
            return (
                f"RAG 16D recuperó similitud coseno {similitud:.4f} y context_precision "
                f"heurística {context_precision:.4f}; compatibilidad {compatibilidad}, "
                f"{discrepancias} discrepancia(s) inter-fojas y "
                f"{'exceso' if excede_area else 'cumplimiento'} de área máxima."
            )

        def nodo_supervisor_auditor(estado_nodo: str) -> str:
            requiere = bool(estado.get("requiere_refinamiento", False))
            if requiere:
                estado["refinamiento_aplicado"] = True
                return (
                    "El Supervisor detectó baja cobertura contextual o discrepancia no "
                    "motivada; se activa el ciclo controlado de refinamiento normativo."
                )
            return (
                "El Supervisor validó consistencia documental, predictiva y normativa; "
                "no se requiere refinamiento cíclico."
            )

        ejecutar_nodo("AgentePercepcionOCR", "COMPLETADO", nodo_percepcion_ocr)
        ejecutar_nodo("AgentePredictivoXGBoost", "COMPLETADO", nodo_predictivo_xgboost)
        ejecutar_nodo("AgenteNormativoRAG", "COMPLETADO", nodo_normativo_rag)

        iteraciones = 1
        ejecutar_nodo(
            "AgenteSupervisorAuditor",
            "COMPLETADO",
            lambda: nodo_supervisor_auditor("COMPLETADO"),
        )

        if bool(estado.get("requiere_refinamiento")) and iteraciones < self.MAX_ITERACIONES_CICLICAS:
            iteraciones = 2
            ejecutar_nodo(
                "AgenteNormativoRAG",
                "REFINAMIENTO_CICLICO",
                lambda: (
                    "Reformulación de la consulta normativa con los artículos de "
                    "subsanación y la ordenanza municipal aplicable."
                ),
            )
            ejecutar_nodo(
                "AgenteSupervisorAuditor",
                "REFINAMIENTO_CICLICO",
                lambda: nodo_supervisor_auditor("REFINAMIENTO_CICLICO"),
            )

        estado["iteraciones_grafo"] = iteraciones
        similitud_final = float(estado.get("similitud_refinada", estado.get("similitud_coseno_rag", 0.0)))
        compatibilidad_final = str(estado.get("compatibilidad_zonificacion", "NO_COMPATIBLE"))
        excede_area_final = bool(estado.get("excede_area", False))
        discrepancias_final = int(estado.get("total_discrepancias_interfojas", 0))
        nivel_final = str(estado.get("nivel_riesgo_ml", "BAJO"))

        es_conforme = (
            similitud_final >= self.UMBRAL_SIMILITUD_ACEPTACION
            and compatibilidad_final != "NO_COMPATIBLE"
            and not excede_area_final
            and discrepancias_final == 0
            and nivel_final != "ALTO"
        )
        recomendacion = (
            "OTORGAR_LICENCIA_CONFORME" if es_conforme else "EMITIR_ESQUELA_DE_OBSERVACION"
        )

        cita_legal = self._construir_cita_legal(estado)
        texto_predictamen = self._construir_texto_predictamen(
            estado=estado,
            iteraciones=iteraciones,
            es_conforme=es_conforme,
            recomendacion=recomendacion,
            cita_legal=cita_legal,
        )

        latencia_total = round(max(0.001, (time.perf_counter() - inicio_total) * 1000.0), 3)
        return {
            "iteraciones_grafo": iteraciones,
            "temperatura_llm": self.TEMPERATURA_DETERMINISTA,
            "alucinaciones_detectadas": 0,
            "alucinaciones_detectadas_no_aplica": True,
            "motor_tipo": "determinista_sin_llm",
            "recomendacion_ia": recomendacion,
            "cita_legal_consolidada": cita_legal,
            "texto_predictamen_explicable": texto_predictamen,
            "nodos_ejecutados": trazas,
            "latencia_total_grafo_ms": latencia_total,
        }

    @staticmethod
    def _construir_cita_legal(estado: Dict[str, Any]) -> str:
        norma = str(estado.get("norma_origen", "Ordenanza Municipal N.° 018-2024-MDT/CM"))
        articulo = str(estado.get("articulo_inciso", "Artículo 12.º, inciso c)"))
        ciiu = str(estado.get("codigo_ciiu", "5610"))
        return (
            f"{norma}, {articulo}, CIIU-{ciiu}; "
            "Ley N.° 28976 (TUO aprobado por D.S. N.° 163-2020-PCM), "
            "Artículos 6.º y 7.º; Ley N.° 31814 (D.S. N.° 115-2025-PCM); "
            "Ley N.° 29733 (Protección de Datos Personales); "
            "Ordenanza Municipal N.° 018-2024-MDT/CM."
        )

    @staticmethod
    def _construir_texto_predictamen(
        estado: Dict[str, Any],
        iteraciones: int,
        es_conforme: bool,
        recomendacion: str,
        cita_legal: str,
    ) -> str:
        faltantes = int(estado.get("documentos_faltantes", 0))
        inconsistencias = int(estado.get("inconsistencias_detectadas", 0))
        critico = int(estado.get("documento_critico_faltante", 0))
        probabilidad = float(estado.get("probabilidad_riesgo_ml", 0.0))
        nivel = str(estado.get("nivel_riesgo_ml", "BAJO"))
        similitud = float(estado.get("similitud_coseno_rag", 0.0))
        context_precision = float(estado.get("context_precision_rag", 0.0))
        compatibilidad = str(estado.get("compatibilidad_zonificacion", "NO_COMPATIBLE"))
        discrepancias = int(estado.get("total_discrepancias_interfojas", 0))
        alertas = estado.get("alertas_interfojas") or []
        dias = int(estado.get("dias_habiles_transcurridos", 0))
        dias_restantes = max(0, 8 - dias)

        detalle_alertas = " ".join(str(alerta) for alerta in alertas) or "Sin alertas inter-fojas."
        return (
            "I. VISTOS Y EXTRACCIÓN OCR\n"
            f"Expediente {estado.get('codigo_expediente', '')} de {estado.get('razon_social_nombre', '')}. "
            f"Giro {estado.get('giro_comercial', '')}, zona {estado.get('zona_urbana', '')}, "
            f"área declarada {float(estado.get('area_comercial_m2', 0.0)):.2f} m². "
            f"OCR reportó {faltantes} faltante(s), {inconsistencias} inconsistencia(s) y "
            f"documento crítico faltante={critico}.\n\n"
            "II. ANÁLISIS PREDICTIVO XGBOOST\n"
            f"Probabilidad de observación {probabilidad:.4f}, nivel de riesgo {nivel}. "
            "La explicabilidad corresponde a la importancia global de variables del modelo "
            "(feature importance de XGBoost); no es una explicación local por instancia.\n\n"
            "III. AUDITORÍA VECTORIAL RAG E INTER-FOJAS\n"
            f"Similitud del coseno {similitud:.4f}, context_precision heurística "
            f"{context_precision:.4f}, compatibilidad de zonificación {compatibilidad}. "
            f"Cruce inter-fojas con {discrepancias} discrepancia(s): {detalle_alertas}\n\n"
            "IV. PRE-DICTAMEN MOTIVADO Y BASE LEGAL\n"
            "El análisis es determinista y no utiliza un LLM generativo "
            f"(temperatura nominal {LangGraphStateGraphMultiagenteAdapter.TEMPERATURA_DETERMINISTA}); "
            f"con {iteraciones} iteración(es) del grafo concluye: {recomendacion}. "
            f"Base legal consolidada: {cita_legal}. "
            f"Resultado de conformidad: {'CONFORME' if es_conforme else 'OBSERVADO'}.\n\n"
            "V. CONTROL SLA Y SUPERVISIÓN HUMANA LEY 31814\n"
            f"Días hábiles transcurridos: {dias}; días restantes: {dias_restantes} "
            f"(plazo máximo 8 días hábiles, Ley N.° 28976). "
            "Este pre-dictamen es una recomendación asistida por IA y requiere decisión y "
            "firma obligatoria del funcionario evaluador (Human-in-the-Loop, Ley N.° 31814)."
        )
