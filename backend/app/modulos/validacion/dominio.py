# -*- coding: utf-8 -*-
"""AR-05 · Dominio del módulo validacion.

Entidades puras: sin SQLAlchemy, FastAPI ni clientes de GitHub Actions. Son el
lenguaje que usan el puerto (puertos.py), el ejecutor falso y el Supervisor
para hablar de una validación funcional (Product Backlog v6.0, tabla `validacion`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

Resultado = Literal["PASS", "FAIL"]


class ValidacionInvalida(ValueError):
    """La solicitud o el resultado de una validación no cumple el contrato."""


@dataclass
class SolicitudValidacion:
    """Qué se verifica: que `elemento_verificar` aparezca en `url_publica`."""

    proyecto_id: int
    url_publica: str
    elemento_verificar: str

    def __post_init__(self) -> None:
        if not self.url_publica.strip() or not self.elemento_verificar.strip():
            raise ValidacionInvalida("url_publica y elemento_verificar son obligatorios.")


@dataclass
class ResultadoValidacion:
    """Resultado de una ejecución E2E; refleja las columnas de la tabla `validacion`.

    - `run_id_actions` es obligatorio (RN-003): identifica la ejecución en GitHub Actions.
    - `captura_url` solo existe cuando el resultado es FAIL (artefacto de la captura).
    """

    proyecto_id: int
    resultado: Resultado
    duracion_ms: int
    ejecutada_en: datetime
    run_id_actions: int
    captura_url: str | None = None

    def __post_init__(self) -> None:
        if self.resultado not in ("PASS", "FAIL"):
            raise ValidacionInvalida("resultado debe ser PASS o FAIL.")
        if self.duracion_ms < 0:
            raise ValidacionInvalida("duracion_ms no puede ser negativa.")
        if self.run_id_actions is None:
            raise ValidacionInvalida("run_id_actions es obligatorio.")
        if self.resultado == "PASS" and self.captura_url is not None:
            raise ValidacionInvalida("Un resultado PASS no lleva captura.")
        if self.ejecutada_en.tzinfo is None:
            raise ValidacionInvalida("ejecutada_en debe incluir zona horaria.")

    def to_dict(self) -> dict:
        datos = asdict(self)
        datos["ejecutada_en"] = self.ejecutada_en.isoformat()
        return datos
