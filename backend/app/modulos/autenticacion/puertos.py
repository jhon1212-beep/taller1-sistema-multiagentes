# -*- coding: utf-8 -*-
"""AR-04 · Puerto del módulo autenticacion.

Contrato que debe cumplir cualquier implementación de autenticación (la
falsa de desarrollo o la real con bcrypt y PostgreSQL). Los demás módulos
solo conocen este Protocol y las entidades de dominio.py.
"""
from __future__ import annotations

from typing import Protocol

from app.modulos.autenticacion.dominio import Docente, Sesion


class ServicioAutenticacion(Protocol):
    def iniciar_sesion(self, correo: str, password: str) -> Sesion:
        """Valida las credenciales y abre una sesión.

        Lanza CredencialesInvalidas si no son correctas.
        """
        ...

    def obtener_docente(self, token: str) -> Docente:
        """Devuelve el docente dueño de una sesión vigente.

        Lanza SesionInvalida si el token no existe, expiró o fue cerrado.
        """
        ...

    def cerrar_sesion(self, token: str) -> None:
        """Invalida el token. Cerrar una sesión inexistente no es un error."""
        ...
