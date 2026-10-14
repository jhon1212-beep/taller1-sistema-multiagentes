# -*- coding: utf-8 -*-
"""TA-017 · FuenteEvidenciaDataset.

Implementa el puerto FuenteEvidencia leyendo el dataset controlado del
proyecto demo. A diferencia de FuenteEvidenciaFalsa (3 ejemplos fijos), aquí
hay 50 evidencias del proyecto 1 y 26 del proyecto 2, con casos que
disparan R1–R4. `referencia` se ignora: el dataset se identifica por
proyecto_id.
"""
from __future__ import annotations

from app.modulos.evidencias.dataset import cargar_evidencias
from app.modulos.evidencias.dominio import Evidencia


class FuenteEvidenciaDataset:
    def __init__(self, fuente: str | None = None) -> None:
        """`fuente` ("github", "notion" o "drive") restringe a un solo tipo,
        para usarla como adaptador de un agente concreto."""
        self._fuente = fuente
        self._evidencias = cargar_evidencias()

    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = None,
        desde: str | None = None,
    ) -> list[Evidencia]:
        res = [
            e for e in self._evidencias
            if e.proyecto_id == proyecto_id
            and (self._fuente is None or e.fuente == self._fuente)
            and (desde is None or (e.fecha or "") > desde)
        ]
        return res[:limite] if limite is not None else res
