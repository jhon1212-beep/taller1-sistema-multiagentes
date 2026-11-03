"""TA-022: armado de las fuentes y del explicador que usa la API de supervisión.

El núcleo (grafo, motor, repositorio) no sabe si las fuentes son reales o de
demostración: aquí se decide con variables de entorno. Así TA-036 (Chávez)
cambia a las fuentes reales sin tocar el Supervisor.

    SUPERVISION_SOURCES = dataset (por defecto) | real
    SUPERVISION_EXPLAINER = template (por defecto) | gemini
"""
from __future__ import annotations

import os
from typing import Mapping

from app.modulos.evidencias.dataset import cargar_evidencias
from app.modulos.evidencias.dominio import Evidencia
from app.modulos.evidencias.puertos import FuenteEvidencia
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.puertos import GeneradorExplicacion

DATASET_PREFIX = "dataset:"


class DemoDatasetSource:
    """Fuente del proyecto demo (TA-017) para una sola fuente.

    La referencia registrada en la tabla fuente tiene la forma "dataset:1"
    (proyecto 1 del dataset). Las evidencias se devuelven con el id real del
    proyecto en la base, que puede no ser 1.
    """

    def __init__(self, source: str) -> None:
        self._source = source
        self._evidences = cargar_evidencias()

    def obtener_evidencias(self, referencia: str, proyecto_id: int, *,
                           limite: int | None = None, desde: str | None = None) -> list[Evidencia]:
        if not referencia.startswith(DATASET_PREFIX):
            raise ValueError(f"Referencia de demostración no válida: {referencia!r}")
        dataset_project = int(referencia[len(DATASET_PREFIX):])
        selected = []
        for evidence in self._evidences:
            if evidence.proyecto_id == dataset_project and evidence.fuente == self._source:
                copy = type(evidence)(**evidence.to_dict())
                copy.proyecto_id = proyecto_id  # se reetiqueta con el id de la base
                selected.append(copy)
        return selected[:limite] if limite is not None else selected


def build_source_adapters(mode: str | None = None) -> Mapping[str, FuenteEvidencia]:
    """Devuelve un adaptador por fuente según el modo pedido."""
    mode = (mode or os.getenv("SUPERVISION_SOURCES", "dataset")).strip().lower()
    if mode == "real":
        # Import diferido: los clientes reales leen tokens del .env al usarse.
        from app.modulos.evidencias.adaptadores.drive.adaptador import FuenteEvidenciaDrive
        from app.modulos.evidencias.adaptadores.github.adaptador import FuenteEvidenciaGitHub
        from app.modulos.evidencias.adaptadores.notion.adaptador import FuenteEvidenciaNotion

        return {
            "github": FuenteEvidenciaGitHub(),
            "notion": FuenteEvidenciaNotion(),
            "drive": FuenteEvidenciaDrive(),
        }
    if mode == "dataset":
        return {source: DemoDatasetSource(source) for source in ("github", "notion", "drive")}
    raise ValueError(f"SUPERVISION_SOURCES no válido: {mode!r} (usa dataset o real)")


def build_explainer(mode: str | None = None) -> GeneradorExplicacion:
    """Plantilla por defecto; Gemini con respaldo de plantilla si se pide."""
    mode = (mode or os.getenv("SUPERVISION_EXPLAINER", "template")).strip().lower()
    fallback = GeneradorExplicacionPlantilla()
    if mode == "gemini":
        from app.modulos.supervision.adaptadores.gemini import GeminiExplanationGenerator
        from app.modulos.supervision.adaptadores.resilient import ResilientExplanationGenerator

        return ResilientExplanationGenerator(GeminiExplanationGenerator(), fallback)
    return fallback
