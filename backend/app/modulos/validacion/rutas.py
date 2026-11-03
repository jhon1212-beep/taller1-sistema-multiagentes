# -*- coding: utf-8 -*-
"""TA-021 · Rutas del módulo validacion.

POST /validaciones   dispara la validación E2E de un proyecto del docente y registra
                     el resultado (PASS/FAIL) en PostgreSQL.

HU-008 · Consulta de la validación funcional (CP-17), solo lectura:

GET  /proyectos/{id}/validaciones          historial (más reciente primero) y recuento
GET  /proyectos/{id}/validaciones/ultima   la validación más reciente (404 si no hay)

El ejecutor se elige con E2E_EJECUTOR: «actions» (por defecto; GitHub Actions, usa
GITHUB_TOKEN y GITHUB_REPO_E2E), «local» (corre e2e/validar-url.mjs aquí) o «falso».
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.compartido.db import obtener_sesion
from app.modulos.autenticacion.rutas import docente_actual
from app.modulos.proyectos.adaptadores.sql import RepositorioProyectosSQL
from app.modulos.proyectos.dominio import ProyectoNoEncontrado
from app.modulos.proyectos.rutas import obtener_servicio as obtener_servicio_proyectos
from app.modulos.proyectos.servicio import ServicioProyectos
from app.modulos.validacion.adaptadores.sql import RepositorioValidacionesSQL
from app.modulos.validacion.dominio import (
    ErrorInfraestructuraValidacion,
    SolicitudValidacion,
    ValidacionGuardada,
    ValidacionInvalida,
)
from app.modulos.validacion.puertos import EjecutorE2E, RepositorioValidaciones
from app.modulos.validacion.revision import LIMITE_MAXIMO
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
        fila_id, r = AgenteValidacion(ejecutor, RepositorioValidacionesSQL(sesion)).validar(solicitud)
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


# -- HU-008 · consulta de la validación funcional -----------------------------
consulta_router = APIRouter(prefix="/proyectos/{proyecto_id}/validaciones", tags=["validacion"])


class ResumenValidacionesOut(BaseModel):
    PASS: int
    FAIL: int


class HistorialValidacionesOut(BaseModel):
    proyecto_id: int
    resumen: ResumenValidacionesOut  # sobre todas las validaciones, no solo las listadas
    items: list[ValidacionOut]  # la más reciente primero


def obtener_repositorio_validaciones(sesion: Session = Depends(obtener_sesion)) -> RepositorioValidaciones:
    """Repositorio real; las pruebas lo reemplazan con el de memoria."""
    return RepositorioValidacionesSQL(sesion)


def _salida(g: ValidacionGuardada) -> ValidacionOut:
    r = g.resultado
    return ValidacionOut(
        id=g.id,
        proyecto_id=r.proyecto_id,
        resultado=r.resultado,
        duracion_ms=r.duracion_ms,
        ejecutada_en=r.ejecutada_en.isoformat(),
        run_id_actions=r.run_id_actions,
        captura_url=r.captura_url,
    )


def _exigir_proyecto_propio(proyectos: ServicioProyectos, docente_id: int, proyecto_id: int) -> None:
    """Un docente solo consulta las validaciones de sus propios proyectos."""
    try:
        proyectos.obtener(docente_id, proyecto_id)
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))


@consulta_router.get("", response_model=HistorialValidacionesOut)
def historial_de_validaciones(
    proyecto_id: int,
    limite: int = Query(20, ge=1, le=LIMITE_MAXIMO),
    resultado: str | None = Query(None, pattern="^(PASS|FAIL)$"),
    docente_id: int = Depends(docente_actual),
    proyectos: ServicioProyectos = Depends(obtener_servicio_proyectos),
    repositorio: RepositorioValidaciones = Depends(obtener_repositorio_validaciones),
):
    _exigir_proyecto_propio(proyectos, docente_id, proyecto_id)
    return HistorialValidacionesOut(
        proyecto_id=proyecto_id,
        resumen=ResumenValidacionesOut(**repositorio.contar(proyecto_id)),
        items=[_salida(g) for g in repositorio.listar(proyecto_id, resultado=resultado, limite=limite)],
    )


@consulta_router.get("/ultima", response_model=ValidacionOut)
def ultima_validacion(
    proyecto_id: int,
    docente_id: int = Depends(docente_actual),
    proyectos: ServicioProyectos = Depends(obtener_servicio_proyectos),
    repositorio: RepositorioValidaciones = Depends(obtener_repositorio_validaciones),
):
    _exigir_proyecto_propio(proyectos, docente_id, proyecto_id)
    ultima = repositorio.ultima(proyecto_id)
    if ultima is None:
        raise HTTPException(status_code=404, detail="El proyecto todavía no tiene validaciones.")
    return _salida(ultima)
