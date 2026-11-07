import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.modulos.autenticacion.rutas import router as autenticacion_router
from app.modulos.evidencias.rutas import router as evidencias_router
from app.modulos.evidencias.rutas_tareas import router as tareas_router
from app.modulos.proyectos.rutas import router as proyectos_router
from app.modulos.validacion.rutas import router as validacion_router
from app.modulos.evidencias.adaptadores.compuesta import FuenteEvidenciaCompuesta
from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa
from app.modulos.evidencias.adaptadores.github.adaptador import FuenteEvidenciaGitHub
from app.modulos.evidencias.adaptadores.notion.adaptador import FuenteEvidenciaNotion
from app.modulos.evidencias.adaptadores.drive.adaptador import FuenteEvidenciaDrive

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Agentes inteligentes para el seguimiento de proyectos de software",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def crear_fuente_evidencias(referencias):
    if os.getenv("FUENTE_EVIDENCIAS", "real") == "falsa":
        return FuenteEvidenciaFalsa()
    return FuenteEvidenciaCompuesta({
        referencias["github"]: FuenteEvidenciaGitHub(),
        referencias["notion"]: FuenteEvidenciaNotion(),
        referencias["drive"]: FuenteEvidenciaDrive(),
    })


@app.middleware("http")
async def agregar_cabeceras_seguridad(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


_origenes = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(autenticacion_router)
app.include_router(proyectos_router)
# HU-004 va antes que las rutas de TA-038 (ambas publican GET /proyectos/{id}/tareas).
app.include_router(tareas_router)
app.include_router(evidencias_router)
app.include_router(validacion_router)


@app.get("/health")
@limiter.limit("5/minute")
def health(request: Request):
    return {"status": "ok"}