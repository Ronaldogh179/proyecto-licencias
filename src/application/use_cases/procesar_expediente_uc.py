from typing import Dict, List
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO
from src.application.ports.input_ports import (
    AutenticarUsuarioInputPort,
    ListarBandejaPriorizadaInputPort,
    ProcesarExpedienteInputPort,
)
from src.application.ports.output_ports import (
    ExpedienteRepositoryPort,
    ExtractorOCRPort,
    PredictorRiesgoPort,
    UsuarioRepositoryPort,
)
from src.domain.entities.expediente import Expediente
from src.domain.factories.expediente_factory import ExpedienteFactory

class AutenticarFuncionarioUseCase(AutenticarUsuarioInputPort):
    def __init__(self, usuario_repo: UsuarioRepositoryPort, token_generator) -> None:
        self._usuario_repo = usuario_repo
        self._token_generator = token_generator

    def autenticar(self, correo: str, password: str, rol: str) -> Dict[str, str]:
        usuario = self._usuario_repo.obtener_por_correo(correo)
        if not usuario or not usuario.tiene_permiso_evaluacion():
            raise PermissionError("Credenciales inválidas o usuario sin permisos municipales.")
        if not self._token_generator.verificar_password(password, usuario.password_hash):
            raise PermissionError("Contraseña incorrecta.")

        token_jwt = self._token_generator.generar_jwt(
            id_usuario=usuario.id_usuario,
            correo=usuario.correo_institucional,
            rol=rol or usuario.rol_operativo,
        )
        return {
            "access_token": token_jwt,
            "token_type": "Bearer",
            "usuario": usuario.nombre_completo,
            "correo": usuario.correo_institucional,
            "rol": rol or usuario.rol_operativo,
        }

class ProcesarExpedientePMV1UseCase(ProcesarExpedienteInputPort):
    def __init__(
        self,
        ocr_port: ExtractorOCRPort,
        predictor_port: PredictorRiesgoPort,
        repository_port: ExpedienteRepositoryPort,
    ) -> None:
        self._ocr_port = ocr_port
        self._predictor_port = predictor_port
        self._repository_port = repository_port

    def ejecutar_flujo_pmv1(self, dto: IngresoExpedienteInputDTO) -> Expediente:
        expediente = ExpedienteFactory.crear_nuevo_expediente(
            codigo_expediente=dto.codigo_expediente,
            dni_ruc_titular=dto.dni_ruc_titular,
            razon_social_nombre=dto.razon_social_nombre,
            giro_comercial=dto.giro_comercial,
            tipo_tramite=dto.tipo_tramite,
            direccion_predio=dto.direccion_predio,
            area_comercial_m2=dto.area_comercial_m2,
            nombre_archivo_pdf=dto.nombre_archivo_pdf,
        )

        resultado_ocr = self._ocr_port.extraer_variables(dto)
        expediente.aplicar_extraccion_ocr(
            faltantes=resultado_ocr.documentos_faltantes,
            inconsistencias=resultado_ocr.inconsistencias_detectadas,
            critico=resultado_ocr.documento_critico_faltante,
            texto_resumen=resultado_ocr.texto_resumen,
            confianza=resultado_ocr.confianza_ocr,
            tiempo_seg=resultado_ocr.tiempo_seg,
        )

        prediccion = self._predictor_port.predecir_riesgo(
            giro_comercial=expediente.giro_comercial,
            tipo_tramite=expediente.tipo_tramite,
            documentos_faltantes=expediente.documentos_faltantes,
            inconsistencias_detectadas=expediente.inconsistencias_detectadas,
            documento_critico_faltante=expediente.documento_critico_faltante,
        )
        expediente.asignar_prediccion_riesgo(
            probabilidad=prediccion.probabilidad_observacion,
            algoritmo=prediccion.nombre_algoritmo,
            importancia=prediccion.importancia_variables,
            latencia_ms=prediccion.latencia_ms,
        )

        return self._repository_port.guardar_expediente(expediente)

class ListarBandejaPriorizadaUseCase(ListarBandejaPriorizadaInputPort):
    def __init__(self, repository_port: ExpedienteRepositoryPort) -> None:
        self._repository_port = repository_port

    def obtener_bandeja_priorizada(self) -> List[Expediente]:
        return self._repository_port.listar_todos_priorizados()
