from fastapi import APIRouter
from pydantic import BaseModel

from src.application.useCases.registrar_expediente import (
    RegistrarExpedienteUseCase,
)


router = APIRouter()


class ExpedienteRequest(BaseModel):
    titular: str
    giro_comercial: str


class MockRepository:
    def guardar(self, expediente) -> None:
        print(f"[BD SIMULADA] Guardando expediente de: {expediente.titular}")


@router.post("/expedientes")
def registrar_expediente(req: ExpedienteRequest):
    repo = MockRepository()
    use_case = RegistrarExpedienteUseCase(repo)
    resultado = use_case.ejecutar(req.titular, req.giro_comercial)
    return {
        "mensaje": "Expediente registrado con éxito",
        "datos": resultado,
    }