# -*- coding: utf-8 -*-
"""TA-017 · FuenteEvidenciaDataset.

Implementa el puerto FuenteEvidencia leyendo el dataset controlado del
proyecto demo. A diferencia de FuenteEvidenciaFalsa (3 ejemplos fijos), aquí
hay 50 evidencias del proyecto 1 y 26 del proyecto 2, con casos que
disparan R1–R4. `referencia` se ignora: el dataset se identifica por
proyecto_id.

Fecha de corte: con `fecha_corte` la fuente se comporta como si el sistema
se hubiera consultado en esa fecha y solo devuelve evidencias con fecha
anterior o igual. Sin ella devuelve todo el dataset (el grafo de TA-015 ya
aplica su propio corte).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.modulos.evidencias.dataset import cargar_evidencias
from app.modulos.evidencias.dominio import Evidencia


def _dt(texto: str) -> datetime:
    d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


class FuenteEvidenciaDataset:
    def __init__(self, fuente: str | None = None, fecha_corte: str | None = None) -> None:
        """`fuente` ("github", "notion" o "drive") restringe a un solo tipo,
        para usarla como adaptador de un agente concreto. `fecha_corte`
        (ISO 8601) descarta las evidencias posteriores."""
        self._fuente = fuente
        self._corte = _dt(fecha_corte) if fecha_corte else None
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
            and (self._corte is None or e.fecha is None or _dt(e.fecha) <= self._corte)
        ]
        return res[:limite] if limite is not None else res
