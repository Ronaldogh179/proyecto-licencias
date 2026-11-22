"""Adaptador de exportación de Acta / Resolución oficial en PDF.

Patrón de Diseño: Adapter (implementa GeneradorActaPDFPort).
Historias de Usuario: PMV3-2-HU10.
"""

from typing import Any

import fitz

from src.application.ports.output_ports import GeneradorActaPDFPort
from src.domain.entities.orquestacion_pmv3 import PreDictamenMultiagentePMV3Domain


class PyMuPDFActaResolutivaAdapter(GeneradorActaPDFPort):
    """Genera un acta A4 en memoria con membrete municipal y firma HITL."""

    ANCHO_A4 = 595
    ALTO_A4 = 842

    def generar_acta_resolutiva_pdf_bytes(
        self,
        predictamen: PreDictamenMultiagentePMV3Domain,
    ) -> bytes:
        documento = fitz.open()
        pagina = documento.new_page(width=self.ANCHO_A4, height=self.ALTO_A4)

        self._insertar_bloque(
            pagina,
            "MUNICIPALIDAD DISTRITAL DE EL TAMBO - HUANCAYO, JUNÍN",
            y=42,
            altura=22,
            tamano=13,
            negrita=True,
            alineacion=1,
        )
        self._insertar_bloque(
            pagina,
            "SUBGERENCIA DE PROMOCIÓN EMPRESARIAL Y COMERCIALIZACIÓN",
            y=64,
            altura=16,
            tamano=9,
            alineacion=1,
        )
        self._insertar_bloque(
            pagina,
            "ACTA DE PRE-DICTAMEN Y RESOLUCIÓN DE FISCALIZACIÓN DOCUMENTAL (SISTEMA SIMEL v3.0)",
            y=82,
            altura=24,
            tamano=10,
            negrita=True,
            alineacion=1,
        )
        pagina.draw_line(fitz.Point(40, 110), fitz.Point(555, 110), color=(0.1, 0.1, 0.1), width=1.2)

        datos = (
            f"EXPEDIENTE: {predictamen.codigo_expediente}\n"
            f"RAZÓN SOCIAL: {predictamen.razon_social_nombre}\n"
            f"GIRO COMERCIAL: {predictamen.giro_comercial}    ZONA URBANA: {predictamen.zona_urbana}\n"
            f"ÁREA DECLARADA: {predictamen.area_comercial_m2:.2f} m²\n"
            f"PROBABILIDAD XGBOOST: {predictamen.probabilidad_riesgo_ml:.4f} "
            f"(RIESGO {predictamen.nivel_riesgo_ml})\n"
            f"SIMILITUD COSENO RAG: {predictamen.similitud_coseno_rag:.4f}    "
            f"CONTEXT PRECISION: {predictamen.context_precision_rag:.4f}\n"
            f"COMPATIBILIDAD ZONIFICACIÓN: {predictamen.compatibilidad_zonificacion}\n"
            f"CRUCE INTER-FOJAS: {'CONFORME' if predictamen.es_conforme_interfojas else 'OBSERVADO'} "
            f"({predictamen.total_discrepancias_interfojas} discrepancia(s))\n"
            f"GRAFO MULTIAGENTE: {predictamen.iteraciones_grafo} iteración(es), "
            f"temperatura {predictamen.temperatura_llm}, "
            f"{predictamen.alucinaciones_detectadas} alucinación(es), "
            f"latencia {predictamen.latencia_total_grafo_ms:.2f} ms\n"
            f"RECOMENDACIÓN IA: {predictamen.recomendacion_ia}"
        )
        self._insertar_bloque(pagina, datos, y=120, altura=150, tamano=8.5)

        self._insertar_bloque(
            pagina,
            "CITA LEGAL CONSOLIDADA",
            y=278,
            altura=14,
            tamano=9,
            negrita=True,
        )
        self._insertar_bloque(
            pagina,
            predictamen.cita_legal_consolidada,
            y=294,
            altura=52,
            tamano=7.8,
        )

        self._insertar_bloque(
            pagina,
            "PRE-DICTAMEN TÉCNICO EXPLICABLE (MULTIAGENTE LANGGRAPH T=0.1)",
            y=350,
            altura=14,
            tamano=9,
            negrita=True,
        )
        self._insertar_bloque(
            pagina,
            predictamen.texto_predictamen_explicable,
            y=366,
            altura=300,
            tamano=7.2,
        )

        self._insertar_bloque(
            pagina,
            "CONTROL DE SLA LEGAL (LEY N.° 28976)",
            y=672,
            altura=14,
            tamano=9,
            negrita=True,
        )
        sla = (
            f"Días hábiles transcurridos: {predictamen.dias_habiles_transcurridos} | "
            f"Días restantes: {predictamen.dias_restantes_sla} | "
            f"Semáforo: {predictamen.estado_semaforo_sla} | "
            f"Cumple SLA (<= 8 días hábiles): {'SÍ' if predictamen.cumple_sla_legal else 'NO'}"
        )
        self._insertar_bloque(pagina, sla, y=688, altura=32, tamano=8)

        pagina.draw_line(fitz.Point(40, 724), fitz.Point(555, 724), color=(0.1, 0.1, 0.1), width=1.0)
        self._insertar_bloque(
            pagina,
            "FIRMA Y DECISIÓN HUMAN-IN-THE-LOOP (LEY N.° 31814)",
            y=732,
            altura=14,
            tamano=9,
            negrita=True,
        )
        firma = (
            f"FUNCIONARIO EVALUADOR: "
            f"{predictamen.funcionario_evaluador_firma or 'PENDIENTE DE FIRMA'}\n"
            f"DECISIÓN FINAL: {predictamen.decision_final_humano}\n"
            f"SUSTENTO ADMINISTRATIVO: "
            f"{predictamen.observaciones_funcionario_hitl or 'Pendiente de revisión humana'}\n"
            f"FECHA DE GENERACIÓN IA: {predictamen.fecha_generacion_ia}\n"
            f"FECHA DE RESOLUCIÓN HITL: "
            f"{predictamen.fecha_resolucion_hitl or 'PENDIENTE'}"
        )
        self._insertar_bloque(pagina, firma, y=748, altura=76, tamano=7.6)

        pdf_bytes = documento.tobytes()
        documento.close()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("La generación del Acta PDF no produjo un documento válido.")
        return pdf_bytes

    @staticmethod
    def _insertar_bloque(
        pagina: Any,
        texto: str,
        y: float,
        altura: float,
        tamano: float,
        negrita: bool = False,
        alineacion: int = 0,
    ) -> None:
        rectangulo = fitz.Rect(40, y, 555, y + altura)
        pagina.insert_textbox(
            rectangulo,
            texto,
            fontsize=tamano,
            fontname="hebo" if negrita else "helv",
            align=alineacion,
            color=(0.05, 0.05, 0.05),
        )
