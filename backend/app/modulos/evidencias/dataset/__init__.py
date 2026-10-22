# -*- coding: utf-8 -*-
"""TA-017 · Carga del dataset controlado del proyecto demo."""
from __future__ import annotations

import json
from pathlib import Path

from app.modulos.evidencias.dominio import Evidencia, EvidenciaDrive, EvidenciaNotion

RUTA_DATASET = Path(__file__).with_name("proyecto_demo.json")


def cargar_dataset() -> dict:
    """Devuelve el JSON completo (proyectos, evidencias, alertas esperadas)."""
    return json.loads(RUTA_DATASET.read_text(encoding="utf-8"))


def _a_evidencia(fila: dict) -> Evidencia:
    comunes = {k: fila[k] for k in ("fuente", "id_externo", "autor", "fecha", "descripcion", "proyecto_id")}
    if fila["fuente"] == "notion":
        return EvidenciaNotion(**comunes, estado=fila["estado"], fecha_limite=fila["fecha_limite"])
    if fila["fuente"] == "drive":
        return EvidenciaDrive(**comunes, tipo_archivo=fila["tipo_archivo"])
    return Evidencia(**comunes)


def cargar_evidencias() -> list[Evidencia]:
    return [_a_evidencia(f) for f in cargar_dataset()["evidencias"]]


def fecha_corte_demo() -> str:
    """Fecha de corte del dataset (ISO 8601, UTC). Las alertas e indicadores
    esperados del JSON están calculados para esta fecha."""
    return cargar_dataset()["fecha_corte"]
