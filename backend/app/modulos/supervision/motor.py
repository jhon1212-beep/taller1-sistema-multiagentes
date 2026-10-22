# -*- coding: utf-8 -*-
"""TA-019 · Motor de indicadores (I1–I4) y reglas de alerta (R1–R4).

Funciones puras: reciben evidencias ya normalizadas y una fecha de corte, y
devuelven indicadores y alertas. No consultan fuentes, no llaman a Gemini ni
persisten nada; eso lo hacen el grafo (TA-015), el generador de explicaciones
(AR-02) y el repositorio.

Definiciones (las descripciones de las reglas son las de
adaptadores/plantilla.py):

    I1  % de tareas en estado "Listo" sobre el total de tareas (None sin tareas)
    I2  % de tareas "Sin empezar" sobre el total de tareas (None sin tareas)
    I3  número de tareas vencidas (las mismas que dispara R1)
    I4  días completos entre la última evidencia de cualquier fuente y el
        corte (None si no hay ninguna evidencia)

    R1  tarea no "Listo" con fecha límite anterior al día del corte (Notion)
    R2  tarea "En curso" sin ediciones en más de 7 días (Notion)
    R3  repositorio sin commits en los 7 días previos al corte (GitHub)
    R4  carpeta sin documentos modificados en los 14 días previos (Drive)

Las evidencias posteriores al corte se ignoran. Una alerta por evidencia y
regla (RN-003: toda alerta lleva su evidencia). R3 y R4 se enlazan a la
evidencia más reciente de su fuente. Si la fuente no tiene evidencias, R3/R4
no se disparan: no hay evidencia a la cual enlazar la alerta.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.supervision.dominio import Alerta, Indicadores

DIAS_R2 = 7
DIAS_R3 = 7
DIAS_R4 = 14


def _dt(texto: str | None) -> datetime | None:
    if not texto:
        return None
    d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _vigentes(evidencias: Iterable[Evidencia], corte: datetime) -> list[Evidencia]:
    """Evidencias con fecha <= corte; las que no tienen fecha se conservan."""
    res = []
    for e in evidencias:
        f = _dt(e.fecha)
        if f is None or f <= corte:
            res.append(e)
    return res


def _tareas(evidencias: list[Evidencia]) -> list[Evidencia]:
    return [e for e in evidencias if e.fuente == "notion"]


def _esta_vencida(tarea: Evidencia, corte: datetime) -> bool:
    limite = getattr(tarea, "fecha_limite", None)
    if getattr(tarea, "estado", None) == "Listo" or not limite:
        return False
    return date.fromisoformat(limite[:10]) < corte.astimezone(timezone.utc).date()


def calcular_indicadores(evidencias: Iterable[Evidencia], fecha_corte: str) -> Indicadores:
    corte = _dt(fecha_corte)
    vigentes = _vigentes(evidencias, corte)
    tareas = _tareas(vigentes)

    if tareas:
        listas = sum(1 for t in tareas if getattr(t, "estado", None) == "Listo")
        sin_empezar = sum(1 for t in tareas if getattr(t, "estado", None) == "Sin empezar")
        i1 = round(100 * listas / len(tareas), 2)
        i2 = round(100 * sin_empezar / len(tareas), 2)
    else:
        i1 = i2 = None

    fechas = [f for f in (_dt(e.fecha) for e in vigentes) if f is not None]
    i4 = (corte - max(fechas)).days if fechas else None

    return {
        "I1": i1,
        "I2": i2,
        "I3": sum(1 for t in tareas if _esta_vencida(t, corte)),
        "I4": i4,
    }


def _alerta(regla: str, fuente: str, evidencia_id: str) -> Alerta:
    return {
        "regla": regla,  # type: ignore[typeddict-item]
        "fuente": fuente,  # type: ignore[typeddict-item]
        "evidencia_ids": [evidencia_id],
        "explicacion": None,  # la completa GeneradorExplicacion
        "origen_explicacion": None,
    }


def evaluar_reglas(evidencias: Iterable[Evidencia], fecha_corte: str) -> list[Alerta]:
    corte = _dt(fecha_corte)
    vigentes = _vigentes(evidencias, corte)
    alertas: list[Alerta] = []

    for t in _tareas(vigentes):
        if _esta_vencida(t, corte):
            alertas.append(_alerta("R1", "notion", t.id_externo))
        editada = _dt(t.fecha)
        if (
            getattr(t, "estado", None) == "En curso"
            and editada is not None
            and editada < corte - timedelta(days=DIAS_R2)
        ):
            alertas.append(_alerta("R2", "notion", t.id_externo))

    for regla, fuente, dias in (("R3", "github", DIAS_R3), ("R4", "drive", DIAS_R4)):
        con_fecha = [(e, _dt(e.fecha)) for e in vigentes if e.fuente == fuente and e.fecha]
        if not con_fecha:
            continue
        ultima, fecha = max(con_fecha, key=lambda par: par[1])
        if fecha < corte - timedelta(days=dias):
            alertas.append(_alerta(regla, fuente, ultima.id_externo))

    return alertas


def evaluar(evidencias: Iterable[Evidencia], fecha_corte: str) -> tuple[Indicadores, list[Alerta]]:
    evidencias = list(evidencias)
    return calcular_indicadores(evidencias, fecha_corte), evaluar_reglas(evidencias, fecha_corte)
