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

@dataclass
class EvidenciaNotion(Evidencia):
    """TA-007: Evidencia + los dos atributos propios de Notion.

    Estado y fecha límite no caben en los 6 campos comunes, pero I1–I3 y
    R1–R2 los necesitan (ver docs/modelo-de-datos.md). GitHub sigue
    usando Evidencia con sus 6 campos.
    """

    estado: str | None = None
    fecha_limite: str | None = None


@dataclass
class EvidenciaDrive(Evidencia):
    """TA-017: Evidencia + el tipo de archivo propio de Drive."""

    tipo_archivo: str | None = None
