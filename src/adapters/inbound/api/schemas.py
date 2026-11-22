"""Esquemas Pydantic compartidos por los routers inbound.

Se extraen aquí para evitar imports entre routers (regla hexagonal).
"""

from typing import Optional

from pydantic import BaseModel


class OrquestarPredictamenRequest(BaseModel):
    codigo_expediente: str
    giro_comercial: str = "Restaurante"
    zona_urbana: str = "RDM"
    area_declarada_tupa_m2: float = 110.5
    area_plano_arquitectura_m2: Optional[float] = None
    dni_ruc_tupa: str = "20601122334"
    dni_ruc_documento_identidad: Optional[str] = None
    direccion_tupa: str = "Av. Huancavelica 1050 - El Tambo"
    direccion_plano: Optional[str] = None
    razon_social_nombre: str = "Administrado MYPE El Tambo S.A.C."
    tipo_tramite: str = "Nueva licencia"
    documentos_faltantes: int = 0
    inconsistencias_detectadas: int = 0
    documento_critico_faltante: int = 0
    dias_habiles_transcurridos: int = 2


class ResolverHITLRequest(BaseModel):
    codigo_expediente: str
    decision_final_humano: str
    funcionario_evaluador: str
    observaciones_funcionario: str
