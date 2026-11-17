"""TA-045: contrato de respuesta de la API de supervisión (TA-022).

Estos modelos solo describen lo que las rutas ya devuelven, para que el
contrato OpenAPI (/openapi.json y docs/api/openapi.json) diga a qué atenerse
al frontend. ``extra="allow"``: un campo nuevo del servicio no se pierde
aunque todavía no esté descrito aquí.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

Fuente = Literal["github", "notion", "drive"]
Regla = Literal["R1", "R2", "R3", "R4", "R5"]
Origen = Literal["gemini", "plantilla"]


class _Abierto(BaseModel):
    model_config = ConfigDict(extra="allow")


class IndicadoresOut(_Abierto):
    """I1 e I2 en %, I3 en tareas, I4 en días. None = sin datos para calcularlo."""

    I1: float | None = None
    I2: float | None = None
    I3: int | None = None
    I4: int | None = None


class EvidenciaOut(_Abierto):
    """Evidencia de origen de una alerta (RN-003)."""

    fuente: Fuente
    id_externo: str
    autor: str | None = None
    fecha: str | None = None
    descripcion: str
    proyecto_id: int
    estado: str | None = None          # solo Notion
    fecha_limite: str | None = None    # solo Notion
    tipo_archivo: str | None = None    # solo Drive


class AlertaOut(_Abierto):
    regla: Regla
    fuente: Fuente
    evidencia_ids: list[str]
    explicacion: str | None = None
    origen_explicacion: Origen | None = None


class AlertaConEvidenciaOut(AlertaOut):
    evidencia: EvidenciaOut | None = None


class FuenteLeidaOut(_Abierto):
    estado: str
    error: str | None = None
    evidencias: int
    fuera_de_corte: int


class GuardadoOut(_Abierto):
    evidencias: int
    alertas: int
    alertas_sin_evidencia: int


class ConsolidacionOut(_Abierto):
    proyecto_id: int
    fecha_corte: str
    fuentes: dict[str, FuenteLeidaOut]
    total_evidencias: int
    indicadores: IndicadoresOut
    alertas: list[AlertaOut]
    guardado: GuardadoOut
    duracion_grafo_ms: float
    duracion_sql_ms: float
    duracion_servicio_ms: float


class IndicadoresCorteOut(_Abierto):
    proyecto_id: int
    fecha_corte: str
    indicadores: IndicadoresOut
    estado_fuentes: dict[str, str]  # ok | fallo | pendiente | no_configurada


class AlertasCorteOut(_Abierto):
    proyecto_id: int
    fecha_corte: str
    total: int
    alertas: list[AlertaConEvidenciaOut]


class ValidacionDelDiaOut(_Abierto):
    resultado: Literal["PASS", "FAIL"]
    duracion_ms: int
    ejecutada_en: str


class CorteOut(_Abierto):
    fecha_corte: str
    indicadores: IndicadoresOut
    total_alertas: int
    alertas_por_regla: dict[str, int]
    validacion: ValidacionDelDiaOut | None = None


class HistorialOut(_Abierto):
    proyecto_id: int
    total_cortes: int
    cortes: list[CorteOut]
