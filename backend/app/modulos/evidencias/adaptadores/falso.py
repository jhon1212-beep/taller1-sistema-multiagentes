# -*- coding: utf-8 -*-
"""AR-01 · FuenteEvidenciaFalsa.

Implementa el puerto FuenteEvidencia sin llamar a ninguna API real. La usa
el módulo supervision (Reyes) para programar el grafo, y el frontend
(Mondragón) para construir las pantallas, mientras los adaptadores reales
de GitHub, Notion y Drive no estén conectados.

Por ahora devuelve datos de ejemplo fijos. Cuando Castro publique el
dataset controlado del proyecto demo (TA-017), esta clase pasa a leerlo de
ahí en vez de tenerlo escrito a mano aquí.
"""
from __future__ import annotations

from app.modulos.evidencias.dominio import Evidencia

_EJEMPLOS = [
    Evidencia(
        fuente="github",
        id_externo="e3a1c9f2b7d4a0158e6f2c9b1d7a4e8f3c2b1a90",
        autor="jhon1212-beep",
        fecha="2026-09-28T14:02:11Z",
        descripcion="TA-001: repositorio y entorno base",
        proyecto_id=1,
    ),
    Evidencia(
        fuente="notion",
        id_externo="pagina-demo-001",
        autor="Henry Mondragón",
        fecha="2026-09-29T10:00:00Z",
        descripcion="Diseñar prototipo de Figma",
        proyecto_id=1,
    ),
    Evidencia(
        fuente="drive",
        id_externo="archivo-demo-001",
        autor="Jhon Castro",
        fecha="2026-09-30T16:30:00Z",
        descripcion="Plan de pruebas Sprint 1.pdf",
        proyecto_id=1,
    ),
]


class FuenteEvidenciaFalsa:
    """Implementación del puerto FuenteEvidencia con datos de ejemplo."""

    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = None,
        desde: str | None = None,
    ) -> list[Evidencia]:
        resultado = [e for e in _EJEMPLOS if e.proyecto_id == proyecto_id]
        if limite is not None:
            resultado = resultado[:limite]
        return resultado
