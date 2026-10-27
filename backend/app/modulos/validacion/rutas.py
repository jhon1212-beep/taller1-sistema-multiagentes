# -*- coding: utf-8 -*-
"""TA-021 · Rutas del módulo validacion.

POST /validaciones   dispara la validación E2E de un proyecto del docente y registra
                     el resultado (PASS/FAIL) en PostgreSQL.

El ejecutor se elige con E2E_EJECUTOR: «actions» (por defecto; GitHub Actions, usa
GITHUB_TOKEN y GITHUB_REPO_E2E), «local» (corre e2e/validar-url.mjs aquí) o «falso».
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.compartido.db import obtener_sesion
from app.modulos.autenticacion.rutas import docente_actual
from app.modulos.proyectos.adaptadores.sql import RepositorioProyectosSQL
from app.modulos.validacion.adaptadores.sql import RegistroValidacionSQL
from app.modulos.validacion.dominio import (
    ErrorInfraestructuraValidacion,
    SolicitudValidacion,
    ValidacionInvalida,
)
from app.modulos.validacion.puertos import EjecutorE2E
from app.modulos.validacion.servicio import AgenteValidacion

router = APIRouter(prefix="/validaciones", tags=["validacion"])


class ValidacionIn(BaseModel):
    proyecto_id: int


class ValidacionOut(BaseModel):
    id: int
    proyecto_id: int
    resultado: str
    duracion_ms: int
    ejecutada_en: str
    run_id_actions: int
    captura_url: str | None = None


def crear_ejecutor() -> EjecutorE2E:
    """Dependencia sustituible en pruebas (app.dependency_overrides)."""
    tipo = os.getenv("E2E_EJECUTOR", "actions").lower()
    if tipo == "falso":
        from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso

        return EjecutorE2EFalso()
    if tipo == "local":
        from app.modulos.validacion.adaptadores.local import EjecutorE2ELocal

        return EjecutorE2ELocal()
    from app.modulos.validacion.adaptadores.github_actions import EjecutorE2EGitHubActions

    try:
        return EjecutorE2EGitHubActions(
            repositorio=os.getenv("GITHUB_REPO_E2E", ""),
            token=os.getenv("GITHUB_TOKEN", ""),
            ref=os.getenv("GITHUB_REF_E2E", "main"),
        )
    except ErrorInfraestructuraValidacion as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.post("", response_model=ValidacionOut, status_code=201)
def validar_proyecto(
    datos: ValidacionIn,
    docente_id: int = Depends(docente_actual),
    sesion: Session = Depends(obtener_sesion),
    ejecutor: EjecutorE2E = Depends(crear_ejecutor),
):
    proyecto = RepositorioProyectosSQL(sesion).obtener(docente_id, datos.proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    try:
        solicitud = SolicitudValidacion(proyecto.id, proyecto.url_publica, proyecto.elemento_verificar)
        fila_id, r = AgenteValidacion(ejecutor, RegistroValidacionSQL(sesion)).validar(solicitud)
    except ValidacionInvalida as error:
        raise HTTPException(status_code=422, detail=str(error))
    except ErrorInfraestructuraValidacion as error:
        raise HTTPException(status_code=502, detail=str(error))
    return ValidacionOut(
        id=fila_id,
        proyecto_id=r.proyecto_id,
        resultado=r.resultado,
        duracion_ms=r.duracion_ms,
        ejecutada_en=r.ejecutada_en.isoformat(),
        run_id_actions=r.run_id_actions,
        captura_url=r.captura_url,
    )
