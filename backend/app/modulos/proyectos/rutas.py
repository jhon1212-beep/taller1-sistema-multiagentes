# -*- coding: utf-8 -*-
"""HU-002 · Rutas del módulo proyectos.

POST   /proyectos                   registrar            (CP-04, CP-05)
GET    /proyectos                   listar los del docente
GET    /proyectos/{id}              ver uno
PUT    /proyectos/{id}              editar
PATCH  /proyectos/{id}/desactivar   desactivar (no se borra)
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.compartido.db import obtener_sesion
from app.modulos.proyectos.adaptadores.sql import RepositorioProyectosSQL
from app.modulos.proyectos.dominio import (
    Integrante,
    Proyecto,
    ProyectoInvalido,
    ProyectoNoEncontrado,
)
from app.modulos.proyectos.servicio import ServicioProyectos

router = APIRouter(prefix="/proyectos", tags=["proyectos"])


# -- esquemas HTTP -----------------------------------------------------------
class IntegranteIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    correo: str | None = Field(default=None, max_length=255)


class FuentesIn(BaseModel):
    github: str = Field(min_length=1, max_length=500)
    notion: str = Field(min_length=1, max_length=500)
    drive: str = Field(min_length=1, max_length=500)


class ProyectoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    curso: str = Field(min_length=1, max_length=100)
    fecha_inicio: date
    fecha_fin: date
    url_publica: str = Field(min_length=1, max_length=500)
    elemento_verificar: str = Field(min_length=1, max_length=255)
    integrantes: list[IntegranteIn] = Field(min_length=1)
    fuentes: FuentesIn


class ProyectoOut(ProyectoIn):
    id: int
    activo: bool


# -- dependencias ------------------------------------------------------------
def docente_actual() -> int:
    """TEMPORAL: devuelve el docente 1 hasta que HU-001 (Castro) entregue el JWT.

    Cuando exista la autenticación, esta función pasa a leer el docente del
    token. El resto del módulo no cambia.
    """
    return 1


def obtener_servicio(sesion: Session = Depends(obtener_sesion)) -> ServicioProyectos:
    return ServicioProyectos(RepositorioProyectosSQL(sesion))


# -- conversiones ------------------------------------------------------------
def _a_dominio(datos: ProyectoIn, docente_id: int) -> Proyecto:
    return Proyecto(
        docente_id=docente_id,
        nombre=datos.nombre,
        curso=datos.curso,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        url_publica=datos.url_publica,
        elemento_verificar=datos.elemento_verificar,
        integrantes=[Integrante(i.nombre, i.correo) for i in datos.integrantes],
        fuentes=datos.fuentes.model_dump(),
    )


def _a_salida(p: Proyecto) -> ProyectoOut:
    return ProyectoOut(
        id=p.id,
        activo=p.activo,
        nombre=p.nombre,
        curso=p.curso,
        fecha_inicio=p.fecha_inicio,
        fecha_fin=p.fecha_fin,
        url_publica=p.url_publica,
        elemento_verificar=p.elemento_verificar,
        integrantes=[IntegranteIn(nombre=i.nombre, correo=i.correo) for i in p.integrantes],
        fuentes=FuentesIn(**p.fuentes),
    )


# -- rutas -------------------------------------------------------------------
@router.post("", response_model=ProyectoOut, status_code=201)
def registrar(
    datos: ProyectoIn,
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
):
    try:
        return _a_salida(servicio.registrar(_a_dominio(datos, docente_id)))
    except ProyectoInvalido as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get("", response_model=list[ProyectoOut])
def listar(
    incluir_inactivos: bool = False,
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
):
    return [_a_salida(p) for p in servicio.listar(docente_id, incluir_inactivos)]


@router.get("/{proyecto_id}", response_model=ProyectoOut)
def ver(
    proyecto_id: int,
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
):
    try:
        return _a_salida(servicio.obtener(docente_id, proyecto_id))
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.put("/{proyecto_id}", response_model=ProyectoOut)
def editar(
    proyecto_id: int,
    datos: ProyectoIn,
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
):
    try:
        return _a_salida(servicio.editar(docente_id, proyecto_id, _a_dominio(datos, docente_id)))
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ProyectoInvalido as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.patch("/{proyecto_id}/desactivar", response_model=ProyectoOut)
def desactivar(
    proyecto_id: int,
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
):
    try:
        return _a_salida(servicio.desactivar(docente_id, proyecto_id))
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
