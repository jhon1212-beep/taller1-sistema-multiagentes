# -*- coding: utf-8 -*-
"""HU-002 · Puerto del módulo proyectos."""
from __future__ import annotations

from typing import Protocol

from app.modulos.proyectos.dominio import Proyecto


class RepositorioProyectos(Protocol):
    def crear(self, proyecto: Proyecto) -> Proyecto: ...

    def listar(self, docente_id: int, incluir_inactivos: bool = False) -> list[Proyecto]: ...

    def obtener(self, docente_id: int, proyecto_id: int) -> Proyecto | None: ...

    def actualizar(self, proyecto: Proyecto) -> Proyecto: ...
