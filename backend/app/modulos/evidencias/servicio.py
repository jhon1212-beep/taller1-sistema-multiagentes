# -*- coding: utf-8 -*-
"""TA-038 · Consultas de evidencias por proyecto y fuente."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compartido.modelos_orm import Evidencia, Fuente, Proyecto


def consultar_fuente(sesion: Session, proyecto_id: int, tipo: str, limite: int | None = None):
    """Devuelve (fuente, evidencias) o None si el proyecto no existe."""
    if sesion.get(Proyecto, proyecto_id) is None:
        return None
    fuente = sesion.scalar(
        select(Fuente).where(Fuente.proyecto_id == proyecto_id, Fuente.tipo == tipo)
    )
    consulta = (
        select(Evidencia)
        .join(Fuente, Fuente.id == Evidencia.fuente_id)
        .where(Evidencia.proyecto_id == proyecto_id, Fuente.tipo == tipo)
        .order_by(Evidencia.fecha.desc())
    )
    if limite:
        consulta = consulta.limit(limite)
    return fuente, list(sesion.scalars(consulta))