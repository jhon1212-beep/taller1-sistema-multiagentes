# -*- coding: utf-8 -*-
"""TA-048 · Reglas de los parámetros de consulta, comunes a todos los repositorios."""
from __future__ import annotations

from app.modulos.validacion.dominio import ValidacionInvalida

LIMITE_MAXIMO = 100


def validar_consulta(resultado: str | None, limite: int) -> None:
    if resultado is not None and resultado not in ("PASS", "FAIL"):
        raise ValidacionInvalida("resultado debe ser PASS o FAIL.")
    if not 1 <= limite <= LIMITE_MAXIMO:
        raise ValidacionInvalida(f"limite debe estar entre 1 y {LIMITE_MAXIMO}.")
