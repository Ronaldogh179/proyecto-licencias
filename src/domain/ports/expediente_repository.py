from abc import ABC, abstractmethod
from src.domain.entities.expediente import Expediente

class ExpedienteRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, expediente: Expediente) -> None:
        pass