from typing import Any, Dict, Tuple

from fastapi import Depends, HTTPException, Request

ROL_EVALUADOR = "EVALUADOR_LICENCIAS"
ROL_MESA_PARTES = "MESA_DE_PARTES"
ROL_ADMIN_TI = "ADMIN_TI"


def obtener_container(request: Request) -> Any:
    return request.app.state.container


def obtener_claims_token(request: Request) -> Dict[str, Any]:
    encabezado = request.headers.get("Authorization", "")
    if not encabezado.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Se requiere un token JWT Bearer para acceder a este recurso.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = encabezado.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="El token JWT Bearer está vacío.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return obtener_container(request).verificador_token.verificar_token(token)
    except PermissionError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        )


def requerir_roles(*roles_permitidos: str):
    roles = tuple(roles_permitidos)

    def _verificar_rol(
        claims: Dict[str, Any] = Depends(obtener_claims_token),
    ) -> Tuple[str, Dict[str, Any]]:
        rol = str(claims.get("role", ""))
        if rol not in roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    "El rol del usuario no tiene permisos para esta operación. "
                    f"Roles permitidos: {', '.join(roles)}."
                ),
            )
        return rol, claims

    return _verificar_rol
