# -*- coding: utf-8 -*-
"""HU-004 · Rutas del módulo evidencias.

GET /proyectos/{id}/tareas   tareas del proyecto desde su base de Notion

El docente y el proyecto se resuelven con los mismos servicios que HU-002,
así que un docente solo consulta las tareas de sus propios proyectos.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.modulos.evidencias.adaptadores.notion.adaptador import FuenteEvidenciaNotion
from app.modulos.evidencias.puertos import FuenteEvidencia
from app.modulos.evidencias.tareas import consultar_tareas
from app.modulos.proyectos.dominio import ProyectoNoEncontrado
from app.modulos.proyectos.rutas import docente_actual, obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos

router = APIRouter(prefix="/proyectos", tags=["evidencias"])

LIMITE_POR_DEFECTO = 100


class TareaOut(BaseModel):
    id: str
    tarea: str
    responsable: str | None
    estado: str | None
    fecha_limite: str | None
    editada: str | None


class ResumenOut(BaseModel):
    listo: int
    en_curso: int
    sin_empezar: int
    sin_responsable: int


class TareasOut(BaseModel):
    proyecto_id: int
    fuente: str
    estado: str  # "ok" | "fallo"
    error: str | None
    total: int
    resumen: ResumenOut
    tareas: list[TareaOut]


def obtener_fuente_tareas() -> FuenteEvidencia:
    """Adaptador real de Notion; las pruebas lo reemplazan con uno falso."""
    return FuenteEvidenciaNotion()


@router.get("/{proyecto_id}/tareas", response_model=TareasOut)
def tareas_del_proyecto(
    proyecto_id: int,
    limite: int = Query(LIMITE_POR_DEFECTO, ge=1, le=200),
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
    fuente: FuenteEvidencia = Depends(obtener_fuente_tareas),
):
    try:
        proyecto = servicio.obtener(docente_id, proyecto_id)
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))

    consulta = consultar_tareas(fuente, proyecto.fuentes["notion"], proyecto.id, limite=limite)
    tareas = consulta.tareas
    return TareasOut(
        proyecto_id=proyecto.id,
        fuente="notion",
        estado=consulta.estado,
        error=consulta.error,
        total=len(tareas),
        resumen=ResumenOut(
            listo=sum(1 for t in tareas if t.estado == "Listo"),
            en_curso=sum(1 for t in tareas if t.estado == "En curso"),
            sin_empezar=sum(1 for t in tareas if t.estado == "Sin empezar"),
            sin_responsable=sum(1 for t in tareas if t.responsable is None),
        ),
        tareas=[TareaOut(**vars(t)) for t in tareas],
    )

class DocumentoOut(BaseModel):
    id: str
    nombre: str
    editor: str
    fecha: str
    tipo: str

class DocumentosOut(BaseModel):
    proyecto_id: int
    fuente: str
    estado: str
    error: str | None
    total: int
    documentos: list[DocumentoOut]

def obtener_fuente_documentos() -> FuenteEvidencia:
    from app.modulos.evidencias.adaptadores.drive.adaptador import FuenteEvidenciaDrive
    return FuenteEvidenciaDrive()

@router.get("/{proyecto_id}/documentos", response_model=DocumentosOut)
def documentos_del_proyecto(
    proyecto_id: int,
    limite: int = Query(LIMITE_POR_DEFECTO, ge=1, le=200),
    docente_id: int = Depends(docente_actual),
    servicio: ServicioProyectos = Depends(obtener_servicio),
    fuente: FuenteEvidencia = Depends(obtener_fuente_documentos),
):
    try:
        proyecto = servicio.obtener(docente_id, proyecto_id)
    except ProyectoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
        
    referencia = proyecto.fuentes.get("drive")
    if not referencia:
        return DocumentosOut(proyecto_id=proyecto.id, fuente="drive", estado="fallo", error="Sin referencia configurada", total=0, documentos=[])
        
    try:
        evidencias = fuente.obtener_evidencias(referencia, proyecto.id, limite=limite)
        docs = [
            DocumentoOut(
                id=e.id_externo,
                nombre=e.descripcion,
                editor=e.autor,
                fecha=e.fecha or "",
                tipo=e.tipo_archivo or "desconocido"
            ) for e in evidencias
        ]
        return DocumentosOut(
            proyecto_id=proyecto.id,
            fuente="drive",
            estado="ok",
            error=None,
            total=len(docs),
            documentos=docs
        )
    except Exception as e:
        return DocumentosOut(
            proyecto_id=proyecto.id,
            fuente="drive",
            estado="fallo",
            error=str(e),
            total=0,
            documentos=[]
        )