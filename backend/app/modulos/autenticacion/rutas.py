# -*- coding: utf-8 -*-
"""HU-001 · Rutas del módulo autenticacion.

POST /auth/login    inicia sesión y devuelve el token
GET  /auth/me       docente de la sesión actual
POST /auth/logout   cierra la sesión

`docente_actual` protege las demás rutas: lee el token Bearer y devuelve el id
del docente (401 si falta o no es válido). `proyectos.rutas.docente_actual`
(temporal) puede reemplazarse por esta función sin tocar el resto del módulo.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.compartido.db import obtener_sesion
from app.modulos.autenticacion.adaptadores.sql import RepositorioDocentesSQL
from app.modulos.autenticacion.dominio import CredencialesInvalidas, Docente, SesionInvalida
from app.modulos.autenticacion.puertos import ServicioAutenticacion
from app.modulos.autenticacion.servicio import ServicioAutenticacionReal

router = APIRouter(prefix="/auth", tags=["autenticacion"])
_esquema = HTTPBearer(auto_error=False)

# Tokens cerrados: compartido por todas las peticiones del proceso.
_SESIONES_CERRADAS: set[str] = set()


class LoginIn(BaseModel):
    correo: str
    password: str


class DocenteOut(BaseModel):
    id: int
    nombre: str
    correo: str


class LoginOut(BaseModel):
    token: str
    tipo: str = "bearer"
    expira_en: str
    docente: DocenteOut


def obtener_servicio_autenticacion(
    sesion: Session = Depends(obtener_sesion),
) -> ServicioAutenticacion:
    """Servicio real; las pruebas lo reemplazan con dependency_overrides."""
    secreto = os.getenv("JWT_SECRET", "")
    if not secreto:
        raise HTTPException(status_code=500, detail="Servidor sin JWT_SECRET configurado.")
    return ServicioAutenticacionReal(
        RepositorioDocentesSQL(sesion), secreto, sesiones_cerradas=_SESIONES_CERRADAS
    )


def _docente_de(
    credenciales: HTTPAuthorizationCredentials | None, servicio: ServicioAutenticacion
) -> Docente:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Falta el token de sesión.")
    try:
        return servicio.obtener_docente(credenciales.credentials)
    except SesionInvalida as error:
        raise HTTPException(status_code=401, detail=str(error))


def docente_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion),
) -> int:
    return _docente_de(credenciales, servicio).id


@router.post("/login", response_model=LoginOut)
def iniciar_sesion(
    datos: LoginIn, servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion)
):
    try:
        sesion = servicio.iniciar_sesion(datos.correo, datos.password)
    except CredencialesInvalidas as error:
        raise HTTPException(status_code=401, detail=str(error))
    docente = servicio.obtener_docente(sesion.token)
    return LoginOut(
        token=sesion.token,
        expira_en=sesion.expira_en.isoformat(),
        docente=DocenteOut(id=docente.id, nombre=docente.nombre, correo=docente.correo),
    )


@router.get("/me", response_model=DocenteOut)
def sesion_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion),
):
    docente = _docente_de(credenciales, servicio)
    return DocenteOut(id=docente.id, nombre=docente.nombre, correo=docente.correo)


@router.post("/logout", status_code=204)
def cerrar_sesion(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion),
):
    if credenciales is not None:
        servicio.cerrar_sesion(credenciales.credentials)
