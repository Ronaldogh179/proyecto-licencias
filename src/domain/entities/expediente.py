from typing import Optional

from pydantic import BaseModel


class Expediente(BaseModel):
    id_expediente: Optional[str] = None
    titular: str
    giro_comercial: str
    estado_predictamen: str = "Pendiente"