"""TA-046: explicar todas las alertas de un corte con el generador que haya.

Lo usan el nodo ``explain`` del grafo y el generador resiliente. Si el
generador sabe trabajar por lote (``generar_lote``), se hace UNA solicitud por
proyecto y corte; si no, se mantiene el comportamiento anterior, una por alerta.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.modulos.supervision.dominio import Alerta, Explicacion


def explicar_en_lote(
    generador: Any,
    alertas: Sequence[Alerta],
    fecha_corte: str,
    contextos: Sequence[Sequence[Mapping[str, Any]]] | None = None,
) -> list[Explicacion]:
    if not alertas:
        return []
    if hasattr(generador, "generar_lote"):
        explicaciones = generador.generar_lote(alertas, fecha_corte, contextos)
        if len(explicaciones) != len(alertas):
            raise ValueError("El generador devolvió un número de explicaciones distinto al de alertas.")
        return list(explicaciones)
    return [
        generador.generar(alerta, fecha_corte, contexto=contextos[i] if contextos else None)
        for i, alerta in enumerate(alertas)
    ]
