# -*- coding: utf-8 -*-
"""HU-001 · RepositorioDocentes sobre la tabla `docente` (PostgreSQL)."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.compartido.modelos_orm import Docente as DocenteORM
from app.modulos.autenticacion.dominio import Docente


def _a_dominio(fila: DocenteORM) -> Docente:
    return Docente(id=fila.id, nombre=fila.nombre, correo=fila.correo, activo=fila.activo)


class RepositorioDocentesSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def buscar_por_correo(self, correo: str) -> tuple[Docente, str] | None:
        fila = self._sesion.scalar(
            select(DocenteORM).where(func.lower(DocenteORM.correo) == correo.strip().lower())
        )
        return (_a_dominio(fila), fila.password_hash) if fila else None

    def obtener(self, docente_id: int) -> Docente | None:
        fila = self._sesion.get(DocenteORM, docente_id)
        return _a_dominio(fila) if fila else None
