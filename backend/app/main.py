from fastapi import FastAPI

from app.modulos.proyectos.rutas import router as proyectos_router

app = FastAPI(
    title="Agentes inteligentes para el seguimiento de proyectos de software",
    version="0.1.0",
)
app.include_router(proyectos_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
