# -*- coding: utf-8 -*-
"""AR-05 · Puerto del módulo validacion.

Contrato de cualquier ejecutor de validaciones E2E (el falso de desarrollo o el
real que dispara el workflow de GitHub Actions). El Supervisor solo conoce este
Protocol y las entidades de dominio.py.
"""
from __future__ import annotations

from typing import Protocol

from app.modulos.validacion.dominio import (
    ResultadoValidacion,
    SolicitudValidacion,
    ValidacionGuardada,
)


class EjecutorE2E(Protocol):
    def ejecutar(self, solicitud: SolicitudValidacion) -> ResultadoValidacion:
        """Ejecuta la validación y devuelve su resultado (PASS o FAIL).

        Un FAIL funcional NO es una excepción: se devuelve como resultado. Las
        excepciones quedan para fallos de infraestructura (p. ej. no se pudo
        disparar el workflow).
        """
        ...


class RepositorioValidaciones(Protocol):
    """TA-048 · Registro y consulta de las validaciones funcionales de un proyecto.

    Las consultas devuelven primero la validación más reciente. Un proyecto sin
    validaciones da `None` (ultima), una lista vacía (listar) o ceros (contar):
    no es un error.
    """

    def registrar(self, resultado: ResultadoValidacion) -> int:
        """Guarda un resultado (PASS o FAIL) y devuelve el id de su fila."""
        ...

    def ultima(self, proyecto_id: int) -> ValidacionGuardada | None:
        """La validación más reciente del proyecto, o None si nunca se validó."""
        ...

    def listar(
        self, proyecto_id: int, *, resultado: str | None = None, limite: int = 20
    ) -> list[ValidacionGuardada]:
        """Historial del proyecto, de la más reciente a la más antigua.

        `resultado` ("PASS" o "FAIL") filtra; `limite` (>= 1) acota. Un valor
        inválido lanza ValidacionInvalida.
        """
        ...

    def contar(self, proyecto_id: int) -> dict[str, int]:
        """{"PASS": n, "FAIL": m} con todas las validaciones del proyecto."""
        ...
