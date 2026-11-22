"""DTOs de aplicación del PMV 3.

Patrón de Diseño: Data Transfer Object (dataclasses puras).
Historias de Usuario: PMV3-1-HU09 y PMV3-2-HU10.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrquestarPreDictamenPMV3InputDTO:
    codigo_expediente: str
    giro_comercial: str
    zona_urbana: str
    area_declarada_tupa_m2: float
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


@dataclass
class ResolverDecisionHITLInputDTO:
    codigo_expediente: str
    decision_final_humano: str
    funcionario_evaluador: str
    observaciones_funcionario: str
