from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO
from src.application.dto.pmv3_dto import (
    OrquestarPreDictamenPMV3InputDTO,
    ResolverDecisionHITLInputDTO,
)
from src.domain.entities.expediente import Expediente

class AutenticarUsuarioInputPort(ABC):
    @abstractmethod
    def autenticar(self, correo: str, password: str, rol: str) -> Dict[str, str]:
        pass

class ProcesarExpedienteInputPort(ABC):
    @abstractmethod
    def ejecutar_flujo_pmv1(self, dto: IngresoExpedienteInputDTO) -> Expediente:
        pass

class ListarBandejaPriorizadaInputPort(ABC):
    @abstractmethod
    def obtener_bandeja_priorizada(self) -> List[Expediente]:
        pass


class OrquestarPreDictamenPMV3InputPort(ABC):
    @abstractmethod
    def ejecutar(self, dto: OrquestarPreDictamenPMV3InputDTO) -> Dict[str, Any]:
        pass


class ResolverDecisionHITLInputPort(ABC):
    @abstractmethod
    def ejecutar_resolucion(self, dto: ResolverDecisionHITLInputDTO) -> Dict[str, Any]:
        pass

    @abstractmethod
    def exportar_acta_pdf(self, codigo_expediente: str) -> Tuple[bytes, str]:
        pass


class ListarPredictamenesPMV3InputPort(ABC):
    @abstractmethod
    def ejecutar(self) -> List[Dict[str, Any]]:
        pass
