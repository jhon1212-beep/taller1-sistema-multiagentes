# -*- coding: utf-8 -*-
"""TA-010 · Servicio de normalización: Evidencia (dominio) -> esquema Pydantic."""
from __future__ import annotations

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.evidencias.esquema import EvidenciaNormalizada

AUTOR_POR_DEFECTO = "sin responsable"
CAMPOS_COMUNES = ("fuente", "id_externo", "autor", "fecha", "descripcion", "proyecto_id")


def normalizar(evidencias: list[Evidencia]) -> list[EvidenciaNormalizada]:
    """Reduce cada evidencia a los 6 campos comunes y los valida.

    Los campos propios de una fuente (estado y fecha_limite de Notion) se
    descartan aquí. Lanza pydantic.ValidationError si falta algún campo común.
    """
    salida = []
    for e in evidencias:
        datos = {k: v for k, v in e.to_dict().items() if k in CAMPOS_COMUNES}
        if not (datos.get("autor") or "").strip():
            datos["autor"] = AUTOR_POR_DEFECTO  # tarea de Notion sin responsable
        salida.append(EvidenciaNormalizada.model_validate(datos))
    return salida