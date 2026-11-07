# -*- coding: utf-8 -*-
"""TA-021 / TA-048 · Repositorio de validaciones en PostgreSQL (tabla `validacion`).

TA-021 solo escribía (`registrar`). TA-048 añade las consultas que necesita la
pantalla de validación funcional (HU-008): la última, el historial y el recuento.
"""
from __future__ import annotations

from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.modulos.validacion.dominio import ResultadoValidacion, ValidacionGuardada
from app.modulos.validacion.revision import validar_consulta


def _a_guardada(fila: orm.Validacion) -> ValidacionGuardada:
    ejecutada = fila.ejecutada_en
    if ejecutada.tzinfo is None:  # SQLite no guarda la zona; PostgreSQL sí
        ejecutada = ejecutada.replace(tzinfo=timezone.utc)
    return ValidacionGuardada(
        id=fila.id,
        resultado=ResultadoValidacion(
            proyecto_id=fila.proyecto_id,
            resultado=fila.resultado,
            duracion_ms=fila.duracion_ms,
            ejecutada_en=ejecutada,
            run_id_actions=fila.run_id_actions,
            captura_url=fila.captura_url,
        ),
    )


class RepositorioValidacionesSQL:
    def __init__(self, sesion: Session):
        self._s = sesion

    def registrar(self, r: ResultadoValidacion) -> int:
        fila = orm.Validacion(
            proyecto_id=r.proyecto_id,
            resultado=r.resultado,
            duracion_ms=r.duracion_ms,
            ejecutada_en=r.ejecutada_en,
            run_id_actions=r.run_id_actions,
            captura_url=r.captura_url,
        )
        self._s.add(fila)
        self._s.commit()
        return fila.id

    def _consulta(self, proyecto_id: int):
        return (
            select(orm.Validacion)
            .where(orm.Validacion.proyecto_id == proyecto_id)
            .order_by(orm.Validacion.ejecutada_en.desc(), orm.Validacion.id.desc())
        )

    def ultima(self, proyecto_id: int) -> ValidacionGuardada | None:
        fila = self._s.scalars(self._consulta(proyecto_id).limit(1)).first()
        return _a_guardada(fila) if fila else None

    def listar(
        self, proyecto_id: int, *, resultado: str | None = None, limite: int = 20
    ) -> list[ValidacionGuardada]:
        validar_consulta(resultado, limite)
        consulta = self._consulta(proyecto_id)
        if resultado:
            consulta = consulta.where(orm.Validacion.resultado == resultado)
        return [_a_guardada(f) for f in self._s.scalars(consulta.limit(limite))]

    def contar(self, proyecto_id: int) -> dict[str, int]:
        filas = self._s.execute(
            select(orm.Validacion.resultado, func.count())
            .where(orm.Validacion.proyecto_id == proyecto_id)
            .group_by(orm.Validacion.resultado)
        ).all()
        recuento = {"PASS": 0, "FAIL": 0}
        recuento.update({resultado: total for resultado, total in filas})
        return recuento


# Nombre de TA-021: las rutas y las pruebas existentes lo siguen importando.
RegistroValidacionSQL = RepositorioValidacionesSQL
