# -*- coding: utf-8 -*-
"""TA-021 · Agente de Validación.

Orquesta el caso de uso: pedir la validación al ejecutor (puerto EjecutorE2E) y
registrar el resultado. No sabe si el ejecutor es el falso, el local o el de GitHub
Actions. Un FAIL funcional se registra igual que un PASS; un fallo de infraestructura
se propaga y NO se registra (no es un resultado de la validación).
"""
from __future__ import annotations

from typing import Protocol

from app.modulos.validacion.dominio import ResultadoValidacion, SolicitudValidacion
from app.modulos.validacion.puertos import EjecutorE2E


class RegistroValidacion(Protocol):
    def registrar(self, resultado: ResultadoValidacion) -> int: ...


class AgenteValidacion:
    def __init__(self, ejecutor: EjecutorE2E, registro: RegistroValidacion):
        self._ejecutor = ejecutor
        self._registro = registro

    def validar(self, solicitud: SolicitudValidacion) -> tuple[int, ResultadoValidacion]:
        """Devuelve (id de la fila registrada, resultado)."""
        resultado = self._ejecutor.ejecutar(solicitud)
        return self._registro.registrar(resultado), resultado
