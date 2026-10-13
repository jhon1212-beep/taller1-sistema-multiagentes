# -*- coding: utf-8 -*-
"""HU-002 · Dominio del módulo proyectos.

Entidades puras: sin SQLAlchemy, FastAPI ni clientes HTTP.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

TIPOS_FUENTE = ("github", "notion", "drive")


class ProyectoInvalido(ValueError):
    """Los datos del proyecto no cumplen las reglas de HU-002."""


class ProyectoNoEncontrado(LookupError):
    """No existe un proyecto con ese id para ese docente."""


@dataclass
class Integrante:
    nombre: str
    correo: str | None = None


@dataclass
class Proyecto:
    docente_id: int
    nombre: str
    curso: str
    fecha_inicio: date
    fecha_fin: date
    url_publica: str
    elemento_verificar: str
    integrantes: list[Integrante]
    fuentes: dict[str, str]  # {"github": ..., "notion": ..., "drive": ...}
    activo: bool = True
    id: int | None = None
