"""AR-02: estado compartido del grafo de supervision."""

from __future__ import annotations

from typing import TypedDict

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.supervision.dominio import (
    Alerta,
    EstadoFuente,
    Fuente,
    Indicadores,
)


class EstadoSupervision(TypedDict):
    """Informacion compartida por los nodos del grafo."""

    proyecto_id: int
    fecha_corte: str
    evidencias: list[Evidencia]
    estado_fuentes: dict[Fuente, EstadoFuente]
    errores_fuentes: dict[Fuente, str | None]
    indicadores: Indicadores
    alertas: list[Alerta]


def crear_estado_inicial(
    proyecto_id: int,
    fecha_corte: str,
) -> EstadoSupervision:
    """Crea un estado independiente para cada ejecucion.

    fecha_corte se recibe en formato ISO 8601.
    No consulta fuentes ni calcula indicadores.
    """
    return {
        "proyecto_id": proyecto_id,
        "fecha_corte": fecha_corte,
        "evidencias": [],
        "estado_fuentes": {
            "github": "pendiente",
            "notion": "pendiente",
            "drive": "pendiente",
        },
        "errores_fuentes": {
            "github": None,
            "notion": None,
            "drive": None,
        },
        "indicadores": {
            "I1": None,
            "I2": None,
            "I3": None,
            "I4": None,
        },
        "alertas": [],
    }