import re
import unicodedata
from typing import List

from src.domain.entities.normativa_rag import ResultadoCruceInterFojasDomain


class AuditorInterFojasService:
    """Servicio puro de dominio para auditar la consistencia documental inter-fojas (PMV2-3-HU08)."""

    TOLERANCIA_AREA_M2 = 5.0

    @staticmethod
    def _normalizar_direccion(direccion: str) -> str:
        texto = unicodedata.normalize("NFKD", (direccion or "").strip().lower())
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r"[^a-z0-9\s]", " ", texto)
        return re.sub(r"\s+", " ", texto).strip()

    @staticmethod
    def auditar_consistencia_documental(
        dni_ruc_formulario: str,
        dni_ruc_plano_dni: str,
        area_formulario_m2: float,
        area_plano_m2: float,
        direccion_formulario: str,
        direccion_plano: str,
    ) -> ResultadoCruceInterFojasDomain:
        alertas: List[str] = []

        dni_ruc_coincide = str(dni_ruc_formulario).strip() == str(dni_ruc_plano_dni).strip()
        if not dni_ruc_coincide:
            alertas.append(
                "Discrepancia de titularidad: El DNI/RUC de la Declaración Jurada TUPA "
                "no coincide con el consignado en planos/documento de identidad."
            )

        diferencia_area = round(abs(float(area_formulario_m2) - float(area_plano_m2)), 2)
        area_coincide = diferencia_area <= AuditorInterFojasService.TOLERANCIA_AREA_M2
        if not area_coincide:
            alertas.append(
                f"Discordancia inter-fojas de metraje: El formulario declara {area_formulario_m2} m² "
                f"pero el plano técnico consigna {area_plano_m2} m² "
                f"(Diferencia: {diferencia_area} m² > límite 5.0 m²)."
            )

        direccion_coincide = (
            AuditorInterFojasService._normalizar_direccion(direccion_formulario)
            == AuditorInterFojasService._normalizar_direccion(direccion_plano)
        )
        if not direccion_coincide:
            alertas.append(
                "Discrepancia de ubicación predial: La dirección consignada en la Declaración "
                "Jurada TUPA no coincide con la dirección del plano técnico."
            )

        total_discrepancias = len(alertas)
        return ResultadoCruceInterFojasDomain(
            dni_ruc_coincide=dni_ruc_coincide,
            area_coincide=area_coincide,
            diferencia_area_m2=diferencia_area,
            direccion_coincide=direccion_coincide,
            total_discrepancias=total_discrepancias,
            alertas_detectadas=alertas,
            es_conforme_cruce=total_discrepancias == 0,
        )
