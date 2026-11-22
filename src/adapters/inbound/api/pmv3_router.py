"""Router HTTP del PMV 3.

Patrón de Diseño: Adapter Inbound (controller) + Pydantic en la frontera HTTP.
Historias de Usuario: PMV3-1-HU09 y PMV3-2-HU10.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.adapters.inbound.api.dependencies import (
    ROL_ADMIN_TI,
    ROL_EVALUADOR,
    ROL_MESA_PARTES,
    obtener_container,
    requerir_roles,
)
from src.adapters.inbound.api.schemas import (
    OrquestarPredictamenRequest,
    ResolverHITLRequest,
)
from src.application.dto.pmv3_dto import (
    OrquestarPreDictamenPMV3InputDTO,
    ResolverDecisionHITLInputDTO,
)
from src.application.use_cases.orquestar_predictamen_pmv3_uc import (
    MECANISMO_PERSISTENCIA_HITL,
    MECANISMO_PERSISTENCIA_PREDICTAMEN,
)

router = APIRouter(prefix="/api/v1/pmv3", tags=["PMV 3 - Multiagente LangGraph & Gobernanza HITL"])

ROLES_OPERACION = (ROL_EVALUADOR, ROL_ADMIN_TI)
ROLES_CONSULTA = (ROL_EVALUADOR, ROL_MESA_PARTES, ROL_ADMIN_TI)


@router.post(
    "/predictamen/orquestar",
    summary="PMV3-1-HU09: Ejecutar StateGraph multiagente de 4 nodos con refinamiento cíclico",
    dependencies=[Depends(requerir_roles(*ROLES_OPERACION))],
)
def orquestar_predictamen_pmv3(req: OrquestarPredictamenRequest, request: Request):
    try:
        container = obtener_container(request)
        dto = OrquestarPreDictamenPMV3InputDTO(**req.model_dump())
        predictamen = container.orquestar_predictamen_pmv3_uc.ejecutar(dto)
        return {
            "status": "success",
            "predictamen": predictamen,
            "procedimiento_almacenado": MECANISMO_PERSISTENCIA_PREDICTAMEN,
            "mecanismo_persistencia": MECANISMO_PERSISTENCIA_PREDICTAMEN,
        }
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get(
    "/predictamenes",
    summary="PMV3-1-HU09: Listar pre-dictámenes multiagente con trazas y estado SLA/HITL",
    dependencies=[Depends(requerir_roles(*ROLES_CONSULTA))],
)
def listar_predictamenes_pmv3(request: Request):
    container = obtener_container(request)
    predictamenes = container.listar_predictamenes_pmv3_uc.ejecutar()
    return {
        "status": "success",
        "total": len(predictamenes),
        "predictamenes": predictamenes,
    }


@router.post(
    "/hitl/resolver",
    summary="PMV3-2-HU10: Registrar decisión y firma obligatoria del funcionario (HITL)",
    dependencies=[Depends(requerir_roles(*ROLES_OPERACION))],
)
def resolver_decision_hitl(req: ResolverHITLRequest, request: Request):
    try:
        container = obtener_container(request)
        dto = ResolverDecisionHITLInputDTO(**req.model_dump())
        predictamen = container.resolver_hitl_pmv3_uc.ejecutar_resolucion(dto)
        return {
            "status": "success",
            "predictamen": predictamen,
            "auditoria_inmutable": True,
            "procedimiento_almacenado": MECANISMO_PERSISTENCIA_HITL,
            "mecanismo_persistencia": MECANISMO_PERSISTENCIA_HITL,
        }
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get(
    "/acta-pdf/{codigo_expediente}",
    summary="PMV3-2-HU10: Exportar Acta / Resolución oficial en PDF con firma HITL",
    dependencies=[Depends(requerir_roles(*ROLES_CONSULTA))],
)
def exportar_acta_pdf(codigo_expediente: str, request: Request):
    try:
        container = obtener_container(request)
        pdf_bytes, nombre_archivo = container.resolver_hitl_pmv3_uc.exportar_acta_pdf(
            codigo_expediente
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            },
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
