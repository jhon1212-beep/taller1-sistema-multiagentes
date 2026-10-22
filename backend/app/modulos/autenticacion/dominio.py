# -*- coding: utf-8 -*-
"""AR-04 · Dominio del módulo autenticacion.

Entidades puras: sin SQLAlchemy, FastAPI, bcrypt ni JWT. Es el lenguaje que
usan el puerto (puertos.py), el adaptador falso y los demás módulos (por
ejemplo `proyectos`, que recibe el `docente_id` de la sesión activa).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class CredencialesInvalidas(ValueError):
    """Correo o contraseña incorrectos, o docente desactivado (HU-001).

    Se usa el mismo error para los tres casos: la respuesta no debe revelar
    si el correo existe.
    """


class SesionInvalida(LookupError):
    """El token no existe, expiró o la sesión ya fue cerrada."""


@dataclass
class Docente:
    """Único usuario directo del MVP. No incluye el hash de la contraseña:
    ese dato nunca sale del adaptador (en la BD es `docente.password_hash`)."""

    id: int
    nombre: str
    correo: str
    activo: bool = True


@dataclass
class Sesion:
    """Sesión abierta tras un inicio de sesión correcto."""

    token: str
    docente_id: int
    emitida_en: datetime
    expira_en: datetime
