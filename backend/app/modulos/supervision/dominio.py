"""AR-02: tipos compartidos del modulo supervision."""

from __future__ import annotations

from typing import Literal, TypedDict


Fuente = Literal["github", "notion", "drive"]
EstadoFuente = Literal["pendiente", "ok", "fallo"]
ReglaAlerta = Literal["R1", "R2", "R3", "R4"]
OrigenExplicacion = Literal["gemini", "plantilla"]


class Indicadores(TypedDict):
    """None representa un indicador aun no calculado."""

    I1: float | None
    I2: float | None
    I3: int | None
    I4: int | None


class Alerta(TypedDict):
    """Alerta asociada a una regla y a evidencias de una fuente."""

    regla: ReglaAlerta
    fuente: Fuente
    evidencia_ids: list[str]
    explicacion: str | None
    origen_explicacion: OrigenExplicacion | None


class Explicacion(TypedDict):
    """Resultado entregado por un generador de explicaciones."""

    texto: str
    origen: OrigenExplicacion