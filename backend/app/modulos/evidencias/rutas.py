# -*- coding: utf-8 -*-
"""TA-038 · Rutas que usan las pestañas GitHub, Notion y Drive del Detalle."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.compartido.db import obtener_sesion
from app.modulos.evidencias import servicio

router = APIRouter(prefix="/proyectos/{proyecto_id}", tags=["evidencias"])

LIMITE_COMMITS = 20


def _responder(proyecto_id, tipo, convertir, sesion, limite=None):
    resultado = servicio.consultar_fuente(sesion, proyecto_id, tipo, limite)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    fuente, evidencias = resultado
    ok = fuente is not None and fuente.estado == "ok"
    return {
        "proyecto_id": proyecto_id,
        "fuente": tipo,
        "estado_fuente": "ok" if ok else "fallo",
        "ultima_extraccion": fuente.ultima_sincronizacion if fuente else None,
        "total": len(evidencias),
        "items": [convertir(e) for e in evidencias],
    }


@router.get("/commits")
def listar_commits(proyecto_id: int, sesion: Session = Depends(obtener_sesion)):
    return _responder(
        proyecto_id, "github",
        lambda e: {"sha": e.id_externo, "autor": e.autor, "fecha": e.fecha, "mensaje": e.descripcion},
        sesion, LIMITE_COMMITS,
    )


@router.get("/tareas")
def listar_tareas(proyecto_id: int, sesion: Session = Depends(obtener_sesion)):
    return _responder(
        proyecto_id, "notion",
        lambda e: {"tarea": e.descripcion, "responsable": e.autor, "estado": e.estado, "fecha_limite": e.fecha_limite},
        sesion,
    )


@router.get("/documentos")
def listar_documentos(proyecto_id: int, sesion: Session = Depends(obtener_sesion)):
    return _responder(
        proyecto_id, "drive",
        lambda e: {"nombre": e.descripcion, "ultimo_editor": e.autor, "fecha": e.fecha, "tipo": e.tipo_archivo},
        sesion,
    )