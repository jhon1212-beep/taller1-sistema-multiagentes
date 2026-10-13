# -*- coding: utf-8 -*-
"""HU-002 · Adaptador falso: repositorio en memoria (pruebas y desarrollo)."""
from __future__ import annotations

from copy import deepcopy

from app.modulos.proyectos.dominio import Proyecto


class RepositorioProyectosMemoria:
    def __init__(self) -> None:
        self._datos: dict[int, Proyecto] = {}
        self._siguiente = 1

    def crear(self, proyecto: Proyecto) -> Proyecto:
        guardado = deepcopy(proyecto)
        guardado.id = self._siguiente
        self._siguiente += 1
        self._datos[guardado.id] = guardado
        return deepcopy(guardado)

    def listar(self, docente_id: int, incluir_inactivos: bool = False) -> list[Proyecto]:
        return [
            deepcopy(p)
            for p in self._datos.values()
            if p.docente_id == docente_id and (incluir_inactivos or p.activo)
        ]

    def obtener(self, docente_id: int, proyecto_id: int) -> Proyecto | None:
        p = self._datos.get(proyecto_id)
        if p is None or p.docente_id != docente_id:
            return None
        return deepcopy(p)

    def actualizar(self, proyecto: Proyecto) -> Proyecto:
        self._datos[proyecto.id] = deepcopy(proyecto)
        return deepcopy(proyecto)
