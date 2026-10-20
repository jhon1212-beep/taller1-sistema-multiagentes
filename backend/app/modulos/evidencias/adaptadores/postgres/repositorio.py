# -*- coding: utf-8 -*-
"""TA-010 · Repositorio de evidencias en PostgreSQL (implementa RepositorioEvidencias)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.compartido.modelos_orm import Evidencia as EvidenciaORM
from app.compartido.modelos_orm import Fuente
from app.modulos.evidencias.esquema import EvidenciaNormalizada


class RepositorioEvidenciasSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def _fuente_id(self, proyecto_id: int, tipo: str) -> int:
        fuente_id = self._sesion.scalar(
            select(Fuente.id).where(
                Fuente.proyecto_id == proyecto_id, Fuente.tipo == tipo
            )
        )
        if fuente_id is None:
            raise LookupError(
                f"El proyecto {proyecto_id} no tiene registrada la fuente '{tipo}'."
            )
        return fuente_id

    def guardar(self, evidencias: list[EvidenciaNormalizada]) -> int:
        """Inserta o actualiza. Reextraer no duplica (UNIQUE fuente_id + id_externo)."""
        for e in evidencias:
            sentencia = insert(EvidenciaORM).values(
                proyecto_id=e.proyecto_id,
                fuente_id=self._fuente_id(e.proyecto_id, e.fuente),
                id_externo=e.id_externo,
                autor=e.autor,
                fecha=e.fecha,
                descripcion=e.descripcion,
            )
            sentencia = sentencia.on_conflict_do_update(
                index_elements=["fuente_id", "id_externo"],
                set_={
                    "autor": sentencia.excluded.autor,
                    "fecha": sentencia.excluded.fecha,
                    "descripcion": sentencia.excluded.descripcion,
                },
            )
            self._sesion.execute(sentencia)
        self._sesion.commit()
        return len(evidencias)

    def listar(
        self, proyecto_id: int, fuente: str | None = None
    ) -> list[EvidenciaNormalizada]:
        consulta = (
            select(EvidenciaORM, Fuente.tipo)
            .join(Fuente, Fuente.id == EvidenciaORM.fuente_id)
            .where(EvidenciaORM.proyecto_id == proyecto_id)
            .order_by(Fuente.tipo, EvidenciaORM.fecha)
        )
        if fuente:
            consulta = consulta.where(Fuente.tipo == fuente)
        return [
            EvidenciaNormalizada(
                fuente=tipo,
                id_externo=fila.id_externo,
                autor=fila.autor or "sin responsable",
                fecha=fila.fecha,
                descripcion=fila.descripcion,
                proyecto_id=fila.proyecto_id,
            )
            for fila, tipo in self._sesion.execute(consulta).all()
        ]