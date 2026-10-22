import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modulos.autenticacion.rutas import router as autenticacion_router
from app.modulos.evidencias.rutas import router as evidencias_router
from app.modulos.proyectos.rutas import router as proyectos_router

app = FastAPI(
    title="Agentes inteligentes para el seguimiento de proyectos de software",
    version="0.1.0",
)

# HU-004: el frontend (Vite, Netlify) vive en otro origen. Los orígenes
# permitidos se configuran con CORS_ORIGINS (separados por coma); por defecto
# solo el servidor de desarrollo de Vite (localhost y 127.0.0.1).
_origenes = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["*"],
)

app.include_router(autenticacion_router)
app.include_router(proyectos_router)
app.include_router(evidencias_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
