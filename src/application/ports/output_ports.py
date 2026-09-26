from abc import ABC, abstractmethod
from typing import List, Optional
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO, ResultadoOCRDTO, ResultadoPrediccionDTO
from src.domain.entities.expediente import Expediente
from src.domain.entities.usuario import Usuario

class ExtractorOCRPort(ABC):
    @abstractmethod
    def extraer_variables(self, dto: IngresoExpedienteInputDTO) -> ResultadoOCRDTO:
        pass

class PredictorRiesgoPort(ABC):
    @abstractmethod
    def predecir_riesgo(
        self,
        giro_comercial: str,
        tipo_tramite: str,
        documentos_faltantes: int,
        inconsistencias_detectadas: int,
        documento_critico_faltante: int,
    ) -> ResultadoPrediccionDTO:
        pass

class ExpedienteRepositoryPort(ABC):
    @abstractmethod
    def guardar_expediente(self, expediente: Expediente) -> Expediente:
        pass

    @abstractmethod
    def listar_todos_priorizados(self) -> List[Expediente]:
        pass

    @abstractmethod
    def obtener_por_codigo(self, codigo_expediente: str) -> Optional[Expediente]:
        pass

class UsuarioRepositoryPort(ABC):
    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        pass
