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
    """PATRÓN DEPENDENCY INJECTION: Contenedor central de Inversión de Control (IoC)."""

    def __init__(self) -> None:
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

container = DependencyContainer()
