# -*- coding: utf-8 -*-
"""TA-021 · Registro de validaciones en PostgreSQL (tabla `validacion`).

Solo escribe. El repositorio completo (consultas e historial) es TA-048.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.modulos.validacion.dominio import ResultadoValidacion


class RegistroValidacionSQL:
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
