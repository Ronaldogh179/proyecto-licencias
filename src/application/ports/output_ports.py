from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO, ResultadoOCRDTO, ResultadoPrediccionDTO
from src.domain.entities.expediente import Expediente
from src.domain.entities.normativa_rag import DictamenAuditoriaPMV2Domain, FragmentoNormativoDomain
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


class MotorRAGZonificacionPort(ABC):
    """Puerto de salida para el motor RAG normativo vectorial (PMV2-1-HU06 / PMV2-2-HU07)."""

    @abstractmethod
    def fragmentar_y_vectorizar_norma(self, texto: str, giro: str, zona: str) -> List[float]:
        pass

    @abstractmethod
    def buscar_similitud_coseno(
        self,
        giro_comercial: str,
        zona_urbana: str,
        area_m2: float,
    ) -> FragmentoNormativoDomain:
        pass


class AuditoriaPMV2RepositoryPort(ABC):
    """Puerto de persistencia híbrida para normativa vectorial y dictámenes PMV2."""

    @abstractmethod
    def guardar_fragmento_normativo(
        self,
        fragmento: FragmentoNormativoDomain,
        vector_embedding: Optional[List[float]] = None,
    ) -> FragmentoNormativoDomain:
        pass

    @abstractmethod
    def listar_fragmentos_normativos(self) -> List[FragmentoNormativoDomain]:
        pass

    @abstractmethod
    def guardar_auditoria_pmv2(
        self,
        dictamen: DictamenAuditoriaPMV2Domain,
    ) -> DictamenAuditoriaPMV2Domain:
        pass

    @abstractmethod
    def listar_auditorias_pmv2(self) -> List[DictamenAuditoriaPMV2Domain]:
        pass

    @abstractmethod
    def validar_zonificacion_rag_coseno(
        self,
        giro_comercial: str,
        zona_urbana: str,
        area_m2: float,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def registrar_auditoria_cruzada_pmv2(
        self,
        dictamen: DictamenAuditoriaPMV2Domain,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def obtener_metricas_pmv1_pmv2(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def ejecutar_carga_masiva_expedientes(self, cantidad: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def guardar_lote_expedientes(self, expedientes: List[Expediente]) -> int:
        pass

    @abstractmethod
    def guardar_lote_auditorias_pmv2(
        self,
        dictamenes: List[DictamenAuditoriaPMV2Domain],
    ) -> int:
        pass
