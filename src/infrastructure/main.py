from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.adapters.inbound.api.expediente_router import router as expediente_router

app = FastAPI(
    title="SIMEL - Municipalidad Distrital de El Tambo (PMV 1)",
    description="Sistema Web con Arquitectura Híbrida Hexagonal para Evaluación y Fiscalización de Licencias con OCR y XGBoost",
    version="1.0.0",
)

app.include_router(expediente_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def render_dashboard():
    html_path = Path("src/adapters/inbound/web_ui/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
