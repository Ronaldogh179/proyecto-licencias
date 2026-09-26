from abc import ABC, abstractmethod
from typing import Dict, List
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO
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
