from unittest.mock import MagicMock
import pytest
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO, ResultadoOCRDTO, ResultadoPrediccionDTO
from src.application.use_cases.procesar_expediente_uc import ProcesarExpedientePMV1UseCase
from src.domain.factories.expediente_factory import ExpedienteFactory
from src.domain.services.calculador_sla import CalculadorSLAService
from src.infrastructure.container import container


def test_hu01_autenticacion_jwt_exitosa_y_bloqueo():
    res = container.auth_use_case.autenticar("evaluador@eltambo.gob.pe", "municipal2026", "EVALUADOR_LICENCIAS")
    assert "access_token" in res
    assert res["rol"] == "EVALUADOR_LICENCIAS"

    with pytest.raises(PermissionError):
        container.auth_use_case.autenticar("intruso@correo.com", "1234", "EVALUADOR_LICENCIAS")

    with pytest.raises(PermissionError):
        container.auth_use_case.autenticar("evaluador@eltambo.gob.pe", "12", "EVALUADOR_LICENCIAS")


def test_hu02_factory_method_y_reglas_sla_dominio():
    exp = ExpedienteFactory.crear_nuevo_expediente(
        codigo_expediente="exp-2026-0999",
        dni_ruc_titular="20601122334",
        razon_social_nombre="Empresa Demo S.A.C.",
        giro_comercial="Restaurante",
        tipo_tramite="Nueva licencia",
        direccion_predio="Jr. Puno 123",
        area_comercial_m2=90.0,
        nombre_archivo_pdf="demo.pdf",
    )
    assert exp.codigo_expediente == "EXP-2026-0999"
    assert CalculadorSLAService.calcular_dias_restantes(exp) == 7
    assert CalculadorSLAService.estado_semaforo_sla(exp) == "DENTRO_DEL_PLAZO_LEGAL"

    exp.dias_habiles_transcurridos = 6
    assert CalculadorSLAService.estado_semaforo_sla(exp) == "ALERTA_PROXIMO_A_VENCER"

    exp.dias_habiles_transcurridos = 10
    assert CalculadorSLAService.estado_semaforo_sla(exp) == "VENCIDO_FUERA_DE_PLAZO"

    with pytest.raises(ValueError):
        ExpedienteFactory.crear_nuevo_expediente("", "20601122334", "Nom", "Restaurante", "Nueva licencia", "Dir", 50.0, "a.pdf")
    with pytest.raises(ValueError):
        ExpedienteFactory.crear_nuevo_expediente("EXP-1", "123", "Nom", "Restaurante", "Nueva licencia", "Dir", 50.0, "a.pdf")
    with pytest.raises(ValueError):
        ExpedienteFactory.crear_nuevo_expediente("EXP-1", "20601122334", "Nom", "GiroInvalido", "Nueva licencia", "Dir", 50.0, "a.pdf")
    with pytest.raises(ValueError):
        ExpedienteFactory.crear_nuevo_expediente("EXP-1", "20601122334", "Nom", "Restaurante", "TramiteInvalido", "Dir", 50.0, "a.pdf")
    with pytest.raises(ValueError):
        ExpedienteFactory.crear_nuevo_expediente("EXP-1", "20601122334", "Nom", "Restaurante", "Nueva licencia", "Dir", -5.0, "a.pdf")


def test_hu03_hu04_hu05_caso_uso_aislado_con_mocks():
    mock_ocr = MagicMock()
    mock_ocr.extraer_variables.return_value = ResultadoOCRDTO(
        documentos_faltantes=2,
        inconsistencias_detectadas=1,
        documento_critico_faltante=1,
        texto_resumen="Texto simulado por Mock OCR",
        confianza_ocr=97.0,
        tiempo_seg=0.05,
    )

    mock_predictor = MagicMock()
    mock_predictor.predecir_riesgo.return_value = ResultadoPrediccionDTO(
        probabilidad_observacion=0.935,
        nombre_algoritmo="MockXGBoost",
        importancia_variables={"documento_critico_faltante": 0.5},
        latencia_ms=0.8,
    )

    mock_repo = MagicMock()
    mock_repo.guardar_expediente.side_effect = lambda e: e

    use_case = ProcesarExpedientePMV1UseCase(
        ocr_port=mock_ocr,
        predictor_port=mock_predictor,
        repository_port=mock_repo,
    )

    dto = IngresoExpedienteInputDTO(
        codigo_expediente="EXP-2026-0777",
        dni_ruc_titular="20556677889",
        razon_social_nombre="Inversiones Mock S.A.C.",
        giro_comercial="Restaurante",
        tipo_tramite="Nueva licencia",
        direccion_predio="Av. Real 500",
        area_comercial_m2=120.0,
        nombre_archivo_pdf="expediente_mock.pdf",
        contenido_pdf_bytes=b"%PDF-1.4 mock",
    )

    resultado = use_case.ejecutar_flujo_pmv1(dto)
    assert resultado.evaluacion_riesgo.nivel_riesgo == "ALTO"
    assert resultado.evaluacion_riesgo.resultado_observacion == 1
    mock_ocr.extraer_variables.assert_called_once()
    mock_predictor.predecir_riesgo.assert_called_once()
    mock_repo.guardar_expediente.assert_called_once()
