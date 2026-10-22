# -*- coding: utf-8 -*-
"""AR-05 · Puerto del módulo validacion.

Contrato de cualquier ejecutor de validaciones E2E (el falso de desarrollo o el
real que dispara el workflow de GitHub Actions). El Supervisor solo conoce este
Protocol y las entidades de dominio.py.
"""
from __future__ import annotations

from typing import Protocol

from app.modulos.validacion.dominio import ResultadoValidacion, SolicitudValidacion


class EjecutorE2E(Protocol):
    def ejecutar(self, solicitud: SolicitudValidacion) -> ResultadoValidacion:
        """Ejecuta la validación y devuelve su resultado (PASS o FAIL).

        Un FAIL funcional NO es una excepción: se devuelve como resultado. Las
        excepciones quedan para fallos de infraestructura (p. ej. no se pudo
        disparar el workflow).
        """
        ...
