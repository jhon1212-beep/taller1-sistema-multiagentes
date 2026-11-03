"""TA-022: caso de uso "ejecutar un corte" y consultas del historial.

Une el grafo del Supervisor (TA-015/TA-023) con el repositorio SQL (TA-018).
No conoce FastAPI: las rutas solo traducen HTTP a estas llamadas.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from app.modulos.evidencias.puertos import FuenteEvidencia
from app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository, cutoff_day
from app.modulos.supervision.grafo.supervisor import (
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.puertos import GeneradorExplicacion

LIMA = ZoneInfo("America/Lima")
RUN_NAME = "TA-022 Consolidation"


def default_cutoff() -> str:
    """Fin del día de hoy en Lima, en ISO 8601 con zona horaria."""
    today = datetime.now(LIMA).date()
    return f"{today.isoformat()}T23:59:59-05:00"


class SupervisionService:
    def __init__(
        self,
        repository: SqlSupervisionRepository,
        adapters: Mapping[str, FuenteEvidencia] | None = None,
        explainer: GeneradorExplicacion | None = None,
    ) -> None:
        # Las consultas (GET) solo necesitan el repositorio; el grafo se arma
        # únicamente cuando se ejecuta un corte.
        self._repo = repository
        self._adapters = adapters
        self._explainer = explainer

    def run_cutoff(self, project_id: int, references: Mapping[str, str],
                   cutoff: str | None = None) -> dict[str, Any]:
        """Ejecuta el grafo completo, guarda el corte y devuelve el consolidado."""
        cutoff = cutoff or default_cutoff()
        initial = build_supervisor_input(project_id, cutoff, references)
        config = {
            "run_name": RUN_NAME,
            "tags": ["TA-022", "consolidation"],
            "metadata": {"project_id": project_id, "cutoff": cutoff},
        }
        if self._adapters is None:
            raise RuntimeError("SupervisionService sin adaptadores: no puede ejecutar cortes.")
        graph = build_supervisor_graph(self._adapters, explainer=self._explainer)
        started = time.perf_counter()
        final = graph.invoke(initial, config=config)
        graph_ms = round((time.perf_counter() - started) * 1000, 1)

        saved = self._repo.guardar(final)
        report = to_consolidated_report(final)
        # La lista completa de evidencias se consulta en /proyectos/{id}/commits, /tareas y /documentos.
        report.pop("evidencias", None)
        return {**report, "guardado": saved, "duracion_grafo_ms": graph_ms}

    def indicators(self, project_id: int, day: str | None) -> dict[str, Any] | None:
        state = self._pick(project_id, day)
        if state is None:
            return None
        return {"proyecto_id": project_id, "fecha_corte": state["fecha_corte"],
                "indicadores": state["indicadores"], "estado_fuentes": state["estado_fuentes"]}

    def alerts(self, project_id: int, day: str | None) -> dict[str, Any] | None:
        state = self._pick(project_id, day)
        if state is None:
            return None
        return {"proyecto_id": project_id, "fecha_corte": state["fecha_corte"],
                "total": len(state["alertas"]), "alertas": state["alertas"]}

    def history(self, project_id: int) -> dict[str, Any]:
        cuts = self._repo.history(project_id)
        return {"proyecto_id": project_id, "total_cortes": len(cuts), "cortes": cuts}

    def _pick(self, project_id: int, day: str | None):
        """Corte del día pedido o, si no se indica, el más reciente."""
        if day:
            return self._repo.obtener(project_id, cutoff_day(day).isoformat())
        cuts = self._repo.listar(project_id)
        return cuts[-1] if cuts else None
