from src.domain.entities.expediente import Expediente
from src.domain.ports.expediente_repository import ExpedienteRepositoryPort


class RegistrarExpedienteUseCase:
    def __init__(self, repository: ExpedienteRepositoryPort):
        self.repository = repository

    def ejecutar(self, titular: str, giro_comercial: str) -> Expediente:
        nuevo_expediente = Expediente(
            titular=titular,
            giro_comercial=giro_comercial,
        )
        self.repository.guardar(nuevo_expediente)
        return nuevo_expediente