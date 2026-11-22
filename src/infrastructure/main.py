from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.adapters.inbound.api.expediente_router import router as expediente_router
from src.adapters.inbound.api.pmv2_router import router as pmv2_router
from src.adapters.inbound.api.pmv3_router import router as pmv3_router
from src.infrastructure.container import container

app = FastAPI(
    title="SIMEL - Municipalidad Distrital de El Tambo (PMV 1 + PMV 2 + PMV 3)",
    description="Sistema Web con Arquitectura Híbrida Hexagonal para Evaluación y Fiscalización de Licencias con OCR, XGBoost, RAG Normativo, Auditoría Inter-Fojas y Orquestación Multiagente HITL",
    version="3.0.0",
)

app.state.container = container

app.include_router(expediente_router)
app.include_router(pmv2_router)
app.include_router(pmv3_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def render_dashboard():
    html_path = Path("src/adapters/inbound/web_ui/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
