from fastapi import FastAPI

from src.infrastructure.adapters.input.api_controller import router as api_router


app = FastAPI(title="API Licencias El Tambo - PMV 1")

# Conectamos el controlador REST que hizo Garcia
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"mensaje": "Estructura Hexagonal Inicializada correctamente"}
