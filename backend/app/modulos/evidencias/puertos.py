# -*- coding: utf-8 -*-
"""AR-01 · Puerto del módulo evidencias.

Contrato que debe cumplir cualquier fuente (GitHub, Notion, Drive, o la
falsa que usan Reyes y Mondragón mientras los agentes reales no están
listos): recibe una referencia (URL de repo, ID de base, ID de carpeta) y
un proyecto, y entrega una lista de Evidencia.
"""
from __future__ import annotations

from typing import Protocol

from app.modulos.evidencias.dominio import Evidencia


class FuenteEvidencia(Protocol):
    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = None,
        desde: str | None = None,
    ) -> list[Evidencia]:
        ...
