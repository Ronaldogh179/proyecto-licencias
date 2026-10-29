from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.application.dto.pmv2_dto import (
    AuditarExpedientePMV2InputDTO,
    GenerarLoteMasivoInputDTO,
    IndexarNormativaInputDTO,
)
from src.infrastructure.container import container

router = APIRouter(prefix="/api/v1/pmv2", tags=["PMV 2 - RAG Normativo y Auditoría Inter-Fojas"])


class IndexarNormativaRequest(BaseModel):
    norma_origen: str
    articulo_inciso: str
    codigo_ciiu: str
    giro_comercial: str
    zona_urbana: str
    compatibilidad: str = "COMPATIBLE"
    area_maxima_m2: float
    texto_fragmento_chunk: str
    tokens_chunk: int = 500
    overlap_tokens: int = 50
    id_fragmento: Optional[str] = None


class AuditarExpedientePMV2Request(BaseModel):
    codigo_expediente: str
    giro_comercial: str
    zona_urbana: str
    dni_ruc_formulario: str
    dni_ruc_plano_dni: str
    area_formulario_m2: float
    area_plano_m2: float
    direccion_formulario: str
    direccion_plano: str


class GenerarLoteMasivoRequest(BaseModel):
    cantidad_transacciones: int = 600


@router.post("/normativa/indexar", summary="PMV2-1-HU06: Indexar fragmento normativo con chunking y vector(16)")
def indexar_normativa(req: IndexarNormativaRequest):
    try:
        dto = IndexarNormativaInputDTO(**req.model_dump())
        fragmento = container.indexar_normativa_uc.ejecutar(dto)
        return {"status": "created", "fragmento": asdict(fragmento)}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.post("/auditorias/auditar", summary="PMV2-2-HU07 y PMV2-3-HU08: RAG de zonificación + cruce inter-fojas")
def auditar_expediente_pmv2(req: AuditarExpedientePMV2Request):
    try:
        dto = AuditarExpedientePMV2InputDTO(**req.model_dump())
        dictamen = container.auditar_pmv2_uc.ejecutar(dto)
        return {"status": "ok", "dictamen": asdict(dictamen)}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get("/auditorias", summary="Listar dictámenes de auditoría PMV2")
def listar_auditorias_pmv2():
    auditorias = container.expediente_repo.listar_auditorias_pmv2()
    return {
        "status": "ok",
        "total": len(auditorias),
        "auditorias": [asdict(dictamen) for dictamen in auditorias],
    }


@router.get("/fragmentos", summary="Listar fragmentos normativos vectorizados")
def listar_fragmentos_normativos():
    fragmentos = container.expediente_repo.listar_fragmentos_normativos()
    return {
        "status": "ok",
        "total": len(fragmentos),
        "fragmentos": [asdict(fragmento) for fragmento in fragmentos],
    }


@router.post("/data-masiva", summary="Generar y evaluar lote masivo de 500 a 1000 expedientes")
def procesar_data_masiva(req: GenerarLoteMasivoRequest):
    try:
        dto = GenerarLoteMasivoInputDTO(cantidad_transacciones=req.cantidad_transacciones)
        metricas = container.data_masiva_uc.ejecutar(dto)
        return {"status": "ok", "metricas": metricas}
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get("/metricas", summary="Métricas consolidadas PMV1 + PMV2")
def obtener_metricas_pmv1_pmv2():
    return {
        "status": "ok",
        "metricas": container.expediente_repo.obtener_metricas_pmv1_pmv2(),
    }
