"""TA-022: API de   consulta consolidada (FastAPI).

POST   /proyectos/{id}/consolidacion   ejecuta   un corte y lo guarda (lo usa corte.yml, TA-033)
GET  /proyectos/{id}/indicadores     I1–I4 del corte   (?fecha_corte=AAAA-MM-DD, por defecto el último)
GET  /proyectos/{id}/alertas         alertas R1–R4 explicadas del corte
GET  /proyectos/{id}/historial       todos los cortes del proyecto (TA-018)

Todas exigen el token JWT de   HU-001 y solo muestran proyectos del docente.
"""
from __future__ import   annotations

from datetime import date
from typing import Any

from fastapi import APIRouter,   Depends, HTTPException, Query
from pydantic import BaseModel,   Field
from sqlalchemy import select
from sqlalchemy.orm import   Session

from app.compartido import   modelos_orm as orm
from app.compartido.db import   obtener_sesion
from   app.modulos.autenticacion.rutas import docente_actual
from   app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository
from   app.modulos.supervision.service import SupervisionService
from   app.modulos.supervision.sources import build_explainer, build_source_adapters

router =   APIRouter(prefix="/proyectos/{proyecto_id}",   tags=["supervision"])


class CutoffIn(BaseModel):
    # ISO 8601 con zona horaria; vacío = fin   del día de hoy en Lima.
    fecha_corte: str | None =   Field(default=None, examples=["2026-10-12T23:59:59-05:00"])


# -- dependencias (las pruebas y   TA-036 pueden reemplazarlas) ---------------
def get_source_adapters():
    return build_source_adapters()


def get_explainer():
    return build_explainer()


def get_service(
    session: Session =   Depends(obtener_sesion),
    adapters=Depends(get_source_adapters),
    explainer=Depends(get_explainer),
) -> SupervisionService:
    return   SupervisionService(SqlSupervisionRepository(session), adapters, explainer)


def get_query_service(session:   Session = Depends(obtener_sesion)) -> SupervisionService:
    """Solo lectura: no arma   fuentes ni explicador (respuestas más rápidas)."""
    return   SupervisionService(SqlSupervisionRepository(session))


def owned_project(
    proyecto_id: int,
    teacher_id: int =   Depends(docente_actual),
    session: Session =   Depends(obtener_sesion),
) -> orm.Proyecto:
    """404 si el proyecto no   existe o es de otro docente (no se revela cuál)."""
    project = session.scalars(
        select(orm.Proyecto).where(
            orm.Proyecto.id == proyecto_id,   orm.Proyecto.docente_id == teacher_id
        )
    ).first()
    if project is None:
        raise HTTPException(status_code=404,   detail="Proyecto no encontrado.")
    return project


def _day(value: str | None)   -> str | None:
    if value is None:
        return None
    try:
        return   date.fromisoformat(value).isoformat()
    except ValueError:
        raise HTTPException(status_code=422,   detail="fecha_corte debe tener el formato AAAA-MM-DD.")


# -- rutas   -------------------------------------------------------------------
@router.post("/consolidacion")
def run_consolidation(
    body: CutoffIn | None = None,
    project: orm.Proyecto =   Depends(owned_project),
    session: Session =   Depends(obtener_sesion),
    service: SupervisionService =   Depends(get_service),
) -> dict[str, Any]:
    if not project.activo:
        raise HTTPException(status_code=409,   detail="El proyecto está desactivado.")
    references = dict(session.execute(
        select(orm.Fuente.tipo,   orm.Fuente.referencia).where(orm.Fuente.proyecto_id == project.id)
    ).all())
    try:
        return service.run_cutoff(project.id,   references, (body.fecha_corte if body else None))
    except ValueError as error:  # fecha de corte mal escrita
        raise HTTPException(status_code=422,   detail=str(error))
    except LookupError as error:  # proyecto sin fuentes registradas
        raise HTTPException(status_code=409,   detail=str(error))


@router.get("/indicadores")
def get_indicators(
    fecha_corte: str | None =   Query(default=None),
    project: orm.Proyecto =   Depends(owned_project),
    service: SupervisionService =   Depends(get_query_service),
) -> dict[str, Any]:
    result = service.indicators(project.id,   _day(fecha_corte))
    if result is None:
        raise HTTPException(status_code=404,   detail="No hay corte para esa fecha.")
    return result


@router.get("/alertas")
def get_alerts(
    fecha_corte: str | None =   Query(default=None),
    project: orm.Proyecto =   Depends(owned_project),
    service: SupervisionService =   Depends(get_query_service),
) -> dict[str, Any]:
    result = service.alerts(project.id,   _day(fecha_corte))
    if result is None:
        raise HTTPException(status_code=404,   detail="No hay corte para esa fecha.")
    return result


@router.get("/historial")
def get_history(
    project: orm.Proyecto =   Depends(owned_project),
    service: SupervisionService =   Depends(get_query_service),
) -> dict[str, Any]:
    return service.history(project.id)
