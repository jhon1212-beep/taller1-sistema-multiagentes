# -*- coding: utf-8 -*-
"""TA-007 · Adaptador real de Notion.

Implementa el puerto FuenteEvidencia (puertos.py) reutilizando el cliente
de EN-002. `referencia` es el ID de la base de datos de tareas.
"""
from __future__ import annotations

from app.modulos.evidencias.adaptadores.notion.cliente import NotionClient, cargar_config
from app.modulos.evidencias.dominio import EvidenciaNotion

LIMITE_TAREAS = 20  # Criterio de aceptación de TA-007: las 20 tareas demo


def _normalizar_tarea(tarea: dict, proyecto_id: int) -> EvidenciaNotion:
    return EvidenciaNotion(
        fuente="notion",
        id_externo=tarea["id"],
        autor=tarea.get("responsable"),  # None si la tarea no tiene responsable
        fecha=tarea.get("editada"),
        descripcion=tarea.get("tarea") or "",
        proyecto_id=proyecto_id,
        estado=tarea.get("estado"),
        fecha_limite=tarea.get("fecha_limite"),
    )


class FuenteEvidenciaNotion:
    """Implementación real del puerto FuenteEvidencia para Notion.

    Puede lanzar NotionError / NotionAuthError; quien la use decide cómo
    manejarlo (ver agentes/agente_notion.py).
    """

    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = LIMITE_TAREAS,
        desde: str | None = None,
    ) -> list[EvidenciaNotion]:
        cliente = NotionClient(token=cargar_config()["token"])
        tareas = cliente.tareas(referencia, desde=desde, maximo=limite)
        return [_normalizar_tarea(t, proyecto_id) for t in tareas]
