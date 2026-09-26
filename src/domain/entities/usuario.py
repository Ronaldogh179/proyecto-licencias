from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Usuario:
    id_usuario: str
    nombre_completo: str
    correo_institucional: str
    password_hash: str
    rol_operativo: str = "EVALUADOR_LICENCIAS"
    estado_activo: bool = True
    fecha_registro: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def tiene_permiso_evaluacion(self) -> bool:
        return self.estado_activo and self.rol_operativo in (
            "EVALUADOR_LICENCIAS",
            "MESA_DE_PARTES",
            "ADMIN_TI",
        )
