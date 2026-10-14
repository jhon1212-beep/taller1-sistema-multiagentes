# -*- coding: utf-8 -*-
"""AR-04 · ServicioAutenticacionFalso.

Implementa el puerto ServicioAutenticacion en memoria, sin base de datos ni
bcrypt, para que `proyectos`, el frontend y las pruebas E2E programen contra
el contrato antes de que exista la autenticación real.

Los docentes de demostración son los mismos del frontend
(frontend/src/datos/demo.js): docente1..docente5@demo.test con la clave
DemoDocente2026!. Son datos de prueba del proyecto, no credenciales reales.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.modulos.autenticacion.dominio import (
    CredencialesInvalidas,
    Docente,
    Sesion,
    SesionInvalida,
)

CLAVE_DEMO = "DemoDocente2026!"
DURACION_SESION = timedelta(hours=8)
_ITERACIONES = 10_000  # suficiente para un adaptador falso; el real usa bcrypt


def _hash(password: str, sal: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, _ITERACIONES)


def _docentes_demo() -> list[tuple[Docente, str]]:
    return [
        (Docente(id=i, nombre=f"Docente {i}", correo=f"docente{i}@demo.test"), CLAVE_DEMO)
        for i in range(1, 6)
    ]


class ServicioAutenticacionFalso:
    def __init__(
        self,
        docentes: list[tuple[Docente, str]] | None = None,
        *,
        ahora: Callable[[], datetime] | None = None,
        duracion: timedelta = DURACION_SESION,
    ) -> None:
        self._ahora = ahora or (lambda: datetime.now(timezone.utc))
        self._duracion = duracion
        self._sal = secrets.token_bytes(16)
        self._docentes: dict[str, Docente] = {}
        self._hashes: dict[str, bytes] = {}
        for docente, password in docentes if docentes is not None else _docentes_demo():
            clave = docente.correo.strip().lower()
            self._docentes[clave] = docente
            self._hashes[clave] = _hash(password, self._sal)
        self._sesiones: dict[str, Sesion] = {}

    def iniciar_sesion(self, correo: str, password: str) -> Sesion:
        clave = correo.strip().lower()
        docente = self._docentes.get(clave)
        # Siempre se calcula el hash para no distinguir "correo inexistente"
        # de "clave incorrecta" por tiempo de respuesta.
        candidato = _hash(password, self._sal)
        esperado = self._hashes.get(clave, b"")
        if docente is None or not docente.activo or not hmac.compare_digest(candidato, esperado):
            raise CredencialesInvalidas("Correo o contraseña incorrectos.")
        emitida = self._ahora()
        sesion = Sesion(
            token=secrets.token_urlsafe(32),
            docente_id=docente.id,
            emitida_en=emitida,
            expira_en=emitida + self._duracion,
        )
        self._sesiones[sesion.token] = sesion
        return Sesion(**vars(sesion))

    def obtener_docente(self, token: str) -> Docente:
        sesion = self._sesiones.get(token)
        if sesion is None:
            raise SesionInvalida("Sesión inexistente o cerrada.")
        if self._ahora() >= sesion.expira_en:
            del self._sesiones[token]
            raise SesionInvalida("La sesión expiró.")
        for docente in self._docentes.values():
            if docente.id == sesion.docente_id:
                return Docente(**vars(docente))
        raise SesionInvalida("El docente de la sesión ya no existe.")

    def cerrar_sesion(self, token: str) -> None:
        self._sesiones.pop(token, None)
