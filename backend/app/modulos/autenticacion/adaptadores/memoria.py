# -*- coding: utf-8 -*-
"""HU-001 · RepositorioDocentes en memoria (pruebas y desarrollo sin PostgreSQL)."""
from __future__ import annotations

from app.modulos.autenticacion.dominio import Docente


class RepositorioDocentesMemoria:
    def __init__(self) -> None:
        self._por_correo: dict[str, tuple[Docente, str]] = {}

    def agregar(self, docente: Docente, password_hash: str) -> None:
        self._por_correo[docente.correo.strip().lower()] = (docente, password_hash)

    def buscar_por_correo(self, correo: str) -> tuple[Docente, str] | None:
        encontrado = self._por_correo.get(correo.strip().lower())
        return (Docente(**vars(encontrado[0])), encontrado[1]) if encontrado else None

    def obtener(self, docente_id: int) -> Docente | None:
        for docente, _ in self._por_correo.values():
            if docente.id == docente_id:
                return Docente(**vars(docente))
        return None
