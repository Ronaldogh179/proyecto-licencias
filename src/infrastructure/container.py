from typing import Any, Optional

from src.adapters.outbound.ml.xgboost_strategy_adapter import (
    EntrenadorModelosPMV1,
    RandomForestStrategyAdapter,
    XGBoostStrategyAdapter,
)
from src.adapters.outbound.ocr.tesseract_ocr_adapter import PyMuPDFTesseractOCRAdapter
from src.adapters.outbound.persistence.supabase_repository_adapter import (
    HybridSupabaseExpedienteRepository,
    InMemoryUsuarioRepository,
)
from src.application.use_cases.procesar_expediente_uc import (
    AutenticarFuncionarioUseCase,
    ListarBandejaPriorizadaUseCase,
    ProcesarExpedientePMV1UseCase,
)
from src.infrastructure.config import JWTTokenGenerator


class DependencyContainer:
    """PATRÓN DEPENDENCY INJECTION: contenedor IoC con Lazy Loading para PMV 2."""

    def __init__(self) -> None:
        self._rag_adapter: Optional[Any] = None
        self._auditor_interfojas_service: Optional[Any] = None
        self._indexar_normativa_uc: Optional[Any] = None
        self._auditar_pmv2_uc: Optional[Any] = None
        self._data_masiva_uc: Optional[Any] = None

        self.entrenador_ml = EntrenadorModelosPMV1()
        self.ocr_adapter = PyMuPDFTesseractOCRAdapter()
        self.xgb_adapter = XGBoostStrategyAdapter(self.entrenador_ml)
        self.rf_adapter = RandomForestStrategyAdapter(self.entrenador_ml)
        self.expediente_repo = HybridSupabaseExpedienteRepository()
        self.usuario_repo = InMemoryUsuarioRepository()

        self.auth_use_case = AutenticarFuncionarioUseCase(
            usuario_repo=self.usuario_repo,
            token_generator=JWTTokenGenerator,
        )
        self.procesar_xgb_use_case = ProcesarExpedientePMV1UseCase(
            ocr_port=self.ocr_adapter,
            predictor_port=self.xgb_adapter,
            repository_port=self.expediente_repo,
        )
        self.procesar_rf_use_case = ProcesarExpedientePMV1UseCase(
            ocr_port=self.ocr_adapter,
            predictor_port=self.rf_adapter,
            repository_port=self.expediente_repo,
        )
        self.listar_bandeja_use_case = ListarBandejaPriorizadaUseCase(
            repository_port=self.expediente_repo,
        )

    @property
    def rag_adapter(self):
        if self._rag_adapter is None:
            from src.adapters.outbound.rag.pgvector_rag_adapter import PgVectorRAGAdapter

            self._rag_adapter = PgVectorRAGAdapter()
        return self._rag_adapter

    @property
    def auditor_interfojas_service(self):
        if self._auditor_interfojas_service is None:
            from src.domain.services.auditor_interfojas_service import AuditorInterFojasService

            self._auditor_interfojas_service = AuditorInterFojasService
        return self._auditor_interfojas_service

    @property
    def indexar_normativa_uc(self):
        if self._indexar_normativa_uc is None:
            from src.application.use_cases.auditar_expediente_pmv2_uc import (
                IndexarNormativaVectorialUseCase,
            )

            self._indexar_normativa_uc = IndexarNormativaVectorialUseCase(
                rag_port=self.rag_adapter,
                repository_port=self.expediente_repo,
            )
        return self._indexar_normativa_uc

    @property
    def auditar_pmv2_uc(self):
        if self._auditar_pmv2_uc is None:
            from src.application.use_cases.auditar_expediente_pmv2_uc import (
                AuditarZonificacionYCrucePMV2UseCase,
            )

            self._auditar_pmv2_uc = AuditarZonificacionYCrucePMV2UseCase(
                rag_port=self.rag_adapter,
                repository_port=self.expediente_repo,
            )
        return self._auditar_pmv2_uc

    @property
    def data_masiva_uc(self):
        if self._data_masiva_uc is None:
            from src.application.use_cases.auditar_expediente_pmv2_uc import (
                ProcesarDataMasivaUseCase,
            )

            self._data_masiva_uc = ProcesarDataMasivaUseCase(
                repository_port=self.expediente_repo,
                predictor_port=self.xgb_adapter,
                rag_port=self.rag_adapter,
                auditoria_use_case=self.auditar_pmv2_uc,
            )
        return self._data_masiva_uc


container = DependencyContainer()
