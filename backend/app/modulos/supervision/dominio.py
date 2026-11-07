"""AR-02: tipos compartidos del modulo supervision."""

from __future__ import annotations

from datetime import date, datetime
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


def cutoff_day(cutoff: str | date) -> date:
    """Día calendario del corte en su propia zona horaria (TA-018).

    "2026-10-12T23:59:59-05:00" es el 12 de octubre en Lima aunque en UTC ya
    sea 13; el docente piensa en el día local. Un corte es único por proyecto
    y día, así que esta regla la comparten el servicio y los repositorios.
    """
    if isinstance(cutoff, date) and not isinstance(cutoff, datetime):
        return cutoff
    text = str(cutoff).strip()
    if len(text) == 10:  # solo "YYYY-MM-DD"
        return date.fromisoformat(text)
    return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
