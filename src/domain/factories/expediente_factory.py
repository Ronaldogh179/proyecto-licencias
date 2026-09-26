import uuid
from src.domain.entities.expediente import Expediente
from src.domain.value_objects.nivel_riesgo import GiroComercialEnum, TipoTramiteEnum

class ExpedienteFactory:
    """PATRÓN FACTORY METHOD: Creación encapsulada de la entidad Expediente."""
    GIROS_VALIDOS = {g.value for g in GiroComercialEnum}
    TRAMITES_VALIDOS = {t.value for t in TipoTramiteEnum}

    @classmethod
    def crear_nuevo_expediente(
        cls,
        codigo_expediente: str,
        dni_ruc_titular: str,
        razon_social_nombre: str,
        giro_comercial: str,
        tipo_tramite: str,
        direccion_predio: str,
        area_comercial_m2: float,
        nombre_archivo_pdf: str,
    ) -> Expediente:
        if not codigo_expediente or not codigo_expediente.strip():
            raise ValueError("El código de expediente TUPA es obligatorio.")
        if len(dni_ruc_titular.strip()) not in (8, 11):
            raise ValueError("El DNI (8 dígitos) o RUC (11 dígitos) es inválido.")
        if giro_comercial not in cls.GIROS_VALIDOS:
            raise ValueError(f"Giro comercial '{giro_comercial}' no válido en TUPA.")
        if tipo_tramite not in cls.TRAMITES_VALIDOS:
            raise ValueError(f"Tipo de trámite '{tipo_tramite}' no válido en TUPA.")
        if area_comercial_m2 <= 0:
            raise ValueError("El área comercial debe ser mayor a 0 m2.")

        return Expediente(
            id_expediente=str(uuid.uuid4()),
            codigo_expediente=codigo_expediente.strip().upper(),
            dni_ruc_titular=dni_ruc_titular.strip(),
            razon_social_nombre=razon_social_nombre.strip(),
            giro_comercial=giro_comercial,
            tipo_tramite=tipo_tramite,
            direccion_predio=direccion_predio.strip(),
            area_comercial_m2=round(float(area_comercial_m2), 2),
            nombre_archivo_pdf=nombre_archivo_pdf,
        )
