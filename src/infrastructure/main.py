from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.adapters.inbound.api.expediente_router import router as expediente_router
from src.adapters.inbound.api.pmv2_router import router as pmv2_router

app = FastAPI(
    title="SIMEL - Municipalidad Distrital de El Tambo (PMV 1 + PMV 2)",
    description="Sistema Web con Arquitectura Híbrida Hexagonal para Evaluación y Fiscalización de Licencias con OCR, XGBoost, RAG Normativo y Auditoría Inter-Fojas",
    version="2.0.0",
)

app.include_router(expediente_router)
app.include_router(pmv2_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def render_dashboard():
    html_path = Path("src/adapters/inbound/web_ui/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
