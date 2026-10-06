"""AR-06: borrador del estado del grafo de supervision."""

from __future__ import annotations

from typing import Literal, TypedDict

from ...evidencias.dominio import Evidencia


Fuente = Literal["github", "notion", "drive"]
EstadoFuente = Literal["pendiente", "ok", "fallo"]
ReglaAlerta = Literal["R1", "R2", "R3", "R4"]


class Indicadores(TypedDict):
    """None indica que el indicador aun no se ha calculado."""

    I1: float | None
    I2: float | None
    I3: int | None
    I4: int | None


class Alerta(TypedDict):
    """Estructura propuesta para una alerta explicable."""

    regla: ReglaAlerta
    fuente: Fuente
    evidencia_ids: list[str]
    explicacion: str | None
    origen_explicacion: Literal["gemini", "plantilla"] | None


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
    Este borrador no consulta APIs ni calcula indicadores.
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