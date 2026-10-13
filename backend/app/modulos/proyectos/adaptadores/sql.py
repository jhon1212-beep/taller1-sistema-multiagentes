# -*- coding: utf-8 -*-
"""HU-002 · Adaptador real: repositorio en PostgreSQL con SQLAlchemy.

Usa las tablas proyecto, integrante y fuente de compartido/modelos_orm.py.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.modulos.proyectos.dominio import Integrante, Proyecto


class RepositorioProyectosSQL:
    def __init__(self, sesion: Session):
        self._s = sesion

    # -- lectura ---------------------------------------------------------
    def _armar(self, fila: orm.Proyecto) -> Proyecto:
        integrantes = self._s.scalars(
            select(orm.Integrante).where(orm.Integrante.proyecto_id == fila.id).order_by(orm.Integrante.id)
        ).all()
        fuentes = self._s.scalars(select(orm.Fuente).where(orm.Fuente.proyecto_id == fila.id)).all()
        return Proyecto(
            id=fila.id,
            docente_id=fila.docente_id,
            nombre=fila.nombre,
            curso=fila.curso,
            fecha_inicio=fila.fecha_inicio,
            fecha_fin=fila.fecha_fin,
            url_publica=fila.url_publica,
            elemento_verificar=fila.elemento_verificar,
            activo=fila.activo,
            integrantes=[Integrante(i.nombre, i.correo) for i in integrantes],
            fuentes={f.tipo: f.referencia for f in fuentes},
        )

    def listar(self, docente_id: int, incluir_inactivos: bool = False) -> list[Proyecto]:
        consulta = select(orm.Proyecto).where(orm.Proyecto.docente_id == docente_id)
        if not incluir_inactivos:
            consulta = consulta.where(orm.Proyecto.activo.is_(True))
        filas = self._s.scalars(consulta.order_by(orm.Proyecto.id)).all()
        return [self._armar(f) for f in filas]

    def obtener(self, docente_id: int, proyecto_id: int) -> Proyecto | None:
        fila = self._s.scalars(
            select(orm.Proyecto).where(
                orm.Proyecto.id == proyecto_id, orm.Proyecto.docente_id == docente_id
            )
        ).first()
        return self._armar(fila) if fila else None

    # -- escritura -------------------------------------------------------
    def _guardar_hijos(self, proyecto_id: int, proyecto: Proyecto) -> None:
        self._s.execute(delete(orm.Integrante).where(orm.Integrante.proyecto_id == proyecto_id))
        self._s.execute(delete(orm.Fuente).where(orm.Fuente.proyecto_id == proyecto_id))
        for i in proyecto.integrantes:
            self._s.add(orm.Integrante(proyecto_id=proyecto_id, nombre=i.nombre.strip(), correo=i.correo))
        for tipo, referencia in proyecto.fuentes.items():
            self._s.add(orm.Fuente(proyecto_id=proyecto_id, tipo=tipo, referencia=referencia.strip()))

    def crear(self, proyecto: Proyecto) -> Proyecto:
        fila = orm.Proyecto(
            docente_id=proyecto.docente_id,
            nombre=proyecto.nombre.strip(),
            curso=proyecto.curso.strip(),
            fecha_inicio=proyecto.fecha_inicio,
            fecha_fin=proyecto.fecha_fin,
            url_publica=proyecto.url_publica.strip(),
            elemento_verificar=proyecto.elemento_verificar.strip(),
        )
        self._s.add(fila)
        self._s.flush()  # obtiene fila.id
        self._guardar_hijos(fila.id, proyecto)
        self._s.commit()
        self._s.refresh(fila)
        return self._armar(fila)

    def actualizar(self, proyecto: Proyecto) -> Proyecto:
        fila = self._s.get(orm.Proyecto, proyecto.id)
        fila.nombre = proyecto.nombre.strip()
        fila.curso = proyecto.curso.strip()
        fila.fecha_inicio = proyecto.fecha_inicio
        fila.fecha_fin = proyecto.fecha_fin
        fila.url_publica = proyecto.url_publica.strip()
        fila.elemento_verificar = proyecto.elemento_verificar.strip()
        fila.activo = proyecto.activo
        self._guardar_hijos(fila.id, proyecto)
        self._s.commit()
        self._s.refresh(fila)
        return self._armar(fila)
