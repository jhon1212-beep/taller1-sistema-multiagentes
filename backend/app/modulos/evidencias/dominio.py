# -*- coding: utf-8 -*-
"""AR-01 · Dominio del módulo evidencias.

Entidad pura: no importa SQLAlchemy, FastAPI ni ningún cliente HTTP. Es el
lenguaje común que usan el puerto (puertos.py), los adaptadores reales
(GitHub, Notion, Drive) y el adaptador falso para hablar de lo mismo.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Evidencia:
    """Los 6 campos comunes de evidencia (Product Backlog v6.0, AR-01):
    fuente, id_externo, autor, fecha, descripción y proyecto."""

    fuente: str  # "github" | "notion" | "drive"
    id_externo: str
    autor: str
    fecha: str | None
    descripcion: str
    proyecto_id: int

    def to_dict(self) -> dict:
        return asdict(self)
