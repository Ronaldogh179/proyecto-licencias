from dataclasses import asdict
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from src.application.dto.expediente_dto import IngresoExpedienteInputDTO
from src.infrastructure.container import container

router = APIRouter(prefix="/api/v1", tags=["PMV 1 - Evaluacion y Fiscalizacion de Licencias"])

class LoginRequest(BaseModel):
    correo: str
    password: str
    rol: str = "EVALUADOR_LICENCIAS"

@router.post("/auth/login", summary="PMV1-1-HU01: Autenticación Institucional JWT")
def login_funcionario(req: LoginRequest):
    try:
        resultado = container.auth_use_case.autenticar(req.correo, req.password, req.rol)
        return {"status": "ok", "data": resultado}
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/expedientes/evaluar", summary="PMV1-2 a HU05: Ingesta PDF + OCR + Predicción ML + Persistencia")
async def evaluar_expediente_pmv1(
    codigo_expediente: str = Form(...),
    dni_ruc_titular: str = Form(...),
    razon_social_nombre: str = Form(...),
    giro_comercial: str = Form(...),
    tipo_tramite: str = Form(...),
    direccion_predio: str = Form("Av. Mariscal Castilla N.° 1200 - El Tambo"),
    area_comercial_m2: float = Form(85.0),
    documentos_faltantes: Optional[int] = Form(None),
    inconsistencias_detectadas: Optional[int] = Form(None),
    documento_critico_faltante: Optional[int] = Form(None),
    algoritmo: str = Form("xgboost"),
    archivo_pdf: Optional[UploadFile] = File(None),
):
    try:
        pdf_bytes = await archivo_pdf.read() if archivo_pdf else b""
        nombre_pdf = archivo_pdf.filename if archivo_pdf and archivo_pdf.filename else f"{codigo_expediente.lower()}.pdf"

        dto = IngresoExpedienteInputDTO(
            codigo_expediente=codigo_expediente,
            dni_ruc_titular=dni_ruc_titular,
            razon_social_nombre=razon_social_nombre,
            giro_comercial=giro_comercial,
            tipo_tramite=tipo_tramite,
            direccion_predio=direccion_predio,
            area_comercial_m2=area_comercial_m2,
            nombre_archivo_pdf=nombre_pdf,
            contenido_pdf_bytes=pdf_bytes,
            documentos_faltantes_manual=documentos_faltantes,
            inconsistencias_manual=inconsistencias_detectadas,
            documento_critico_manual=documento_critico_faltante,
            algoritmo_preferido=algoritmo,
        )

        use_case = (
            container.procesar_rf_use_case
            if algoritmo.lower() == "random_forest"
            else container.procesar_xgb_use_case
        )
        expediente = use_case.ejecutar_flujo_pmv1(dto)
        return {"status": "created", "expediente": asdict(expediente)}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/expedientes/bandeja", summary="PMV1-5-HU05: Listar Bandeja Priorizada por Riesgo ML")
def listar_bandeja_priorizada():
    lista = container.listar_bandeja_use_case.obtener_bandeja_priorizada()
    return {
        "status": "ok",
        "total": len(lista),
        "metricas_modelos_poc": container.entrenador_ml.metricas_poc,
        "expedientes": [asdict(e) for e in lista],
    }
