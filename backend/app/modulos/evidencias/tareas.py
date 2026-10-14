# -*- coding: utf-8 -*-
"""HU-004 · Consulta de tareas de un proyecto (vista de tareas de Notion).

Orquesta una FuenteEvidencia y devuelve las tareas ya normalizadas. Si la
fuente falla (credenciales rechazadas, red, Notion caído) no se inventan
tareas: el resultado queda en estado "fallo" con un mensaje legible, igual
que el agente de TA-007 y el consolidado de TA-015.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modulos.evidencias.adaptadores.notion.cliente import NotionAuthError, NotionError
from app.modulos.evidencias.puertos import FuenteEvidencia


@dataclass
class Tarea:
    id: str
    tarea: str
    responsable: str | None  # None: tarea sin responsable (riesgo del Charter)
    estado: str | None  # Sin empezar | En curso | Listo
    fecha_limite: str | None
    editada: str | None


@dataclass
class ConsultaTareas:
    estado: str  # "ok" | "fallo"
    tareas: list[Tarea] = field(default_factory=list)
    error: str | None = None


def consultar_tareas(
    fuente: FuenteEvidencia,
    referencia: str,
    proyecto_id: int,
    *,
    limite: int | None = None,
) -> ConsultaTareas:
    try:
        evidencias = fuente.obtener_evidencias(referencia, proyecto_id, limite=limite)
    except NotionAuthError:
        return ConsultaTareas(
            "fallo",
            error="Integración fallida: Notion rechazó las credenciales. No se cargaron tareas.",
        )
    except NotionError as error:
        return ConsultaTareas("fallo", error=f"Integración fallida: Notion. {error}")

    tareas = [
        Tarea(
            id=e.id_externo,
            tarea=e.descripcion,
            responsable=e.autor,
            estado=getattr(e, "estado", None),
            fecha_limite=getattr(e, "fecha_limite", None),
            editada=e.fecha,
        )
        for e in evidencias
        if e.fuente == "notion"
    ]
    return ConsultaTareas("ok", tareas)
