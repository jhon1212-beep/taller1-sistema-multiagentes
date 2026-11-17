# -*- coding: utf-8 -*-
"""HU-002 · Servicio del módulo proyectos: reglas de negocio.

Depende solo del puerto RepositorioProyectos, no de la base de datos.
"""
from __future__ import annotations

from dataclasses import replace

from app.modulos.proyectos.dominio import (
    FUENTES_OBLIGATORIAS,
    TIPOS_FUENTE,
    Proyecto,
    ProyectoInvalido,
    ProyectoNoEncontrado,
)
from app.modulos.proyectos.puertos import RepositorioProyectos


def validar(proyecto: Proyecto) -> None:
    """Reglas de HU-002 (CP-04 y CP-05)."""
    if not proyecto.nombre.strip():
        raise ProyectoInvalido("El nombre del proyecto es obligatorio.")
    if not proyecto.curso.strip():
        raise ProyectoInvalido("El curso es obligatorio.")
    if proyecto.fecha_fin < proyecto.fecha_inicio:
        raise ProyectoInvalido("La fecha de fin no puede ser anterior a la de inicio.")
    if not proyecto.integrantes:
        raise ProyectoInvalido("El proyecto necesita al menos 1 integrante.")
    if any(not i.nombre.strip() for i in proyecto.integrantes):
        raise ProyectoInvalido("Todos los integrantes deben tener nombre.")
    for tipo in FUENTES_OBLIGATORIAS:
        if not (proyecto.fuentes.get(tipo) or "").strip():
            raise ProyectoInvalido(f"Falta la referencia de la fuente {tipo}.")
    desconocidas = set(proyecto.fuentes) - set(TIPOS_FUENTE)
    if desconocidas:
        raise ProyectoInvalido(f"Fuente no admitida: {', '.join(sorted(desconocidas))}.")
    if not proyecto.url_publica.startswith(("http://", "https://")):
        raise ProyectoInvalido("La URL pública debe empezar con http:// o https://.")
    if not proyecto.elemento_verificar.strip():
        raise ProyectoInvalido("El elemento a verificar es obligatorio.")


def _sin_fuentes_vacias(proyecto: Proyecto) -> Proyecto:
    """Drive es opcional: una referencia vacía equivale a no registrarla."""
    fuentes = {t: r.strip() for t, r in proyecto.fuentes.items() if r and r.strip()}
    return replace(proyecto, fuentes=fuentes)


class ServicioProyectos:
    def __init__(self, repositorio: RepositorioProyectos):
        self._repo = repositorio

    def registrar(self, proyecto: Proyecto) -> Proyecto:
        proyecto = _sin_fuentes_vacias(proyecto)
        validar(proyecto)
        return self._repo.crear(proyecto)

    def listar(self, docente_id: int, incluir_inactivos: bool = False) -> list[Proyecto]:
        return self._repo.listar(docente_id, incluir_inactivos)

    def obtener(self, docente_id: int, proyecto_id: int) -> Proyecto:
        proyecto = self._repo.obtener(docente_id, proyecto_id)
        if proyecto is None:
            raise ProyectoNoEncontrado(f"Proyecto {proyecto_id} no encontrado.")
        return proyecto

    def editar(self, docente_id: int, proyecto_id: int, nuevo: Proyecto) -> Proyecto:
        actual = self.obtener(docente_id, proyecto_id)
        cambiado = _sin_fuentes_vacias(
            replace(nuevo, id=actual.id, docente_id=actual.docente_id, activo=actual.activo)
        )
        validar(cambiado)
        return self._repo.actualizar(cambiado)

    def desactivar(self, docente_id: int, proyecto_id: int) -> Proyecto:
        actual = self.obtener(docente_id, proyecto_id)
        return self._repo.actualizar(replace(actual, activo=False))
