"""TA-023: ejecuta el Supervisor y guarda alertas con explicaciones."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

from langsmith import Client, tracing_context  # noqa: E402
from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset  # noqa: E402
from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa  # noqa: E402
from app.modulos.supervision.adaptadores.gemini import GeminiExplanationGenerator  # noqa: E402
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla  # noqa: E402
from app.modulos.supervision.adaptadores.resilient import ResilientExplanationGenerator  # noqa: E402
from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)

RUN_NAME = "TA-023 Explainable alerts"
REFERENCES = {"github": "repo-demo", "notion": "base-demo", "drive": "folder-demo"}


class FailingSource:
    """Simula un error de una fuente para comprobar la degradación."""
    def __init__(self, source: str) -> None:
        self.source = source

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        raise ConnectionError(f"{self.source} is unavailable (simulated)")


class FakeRateLimitLLM:
    """Simula que Gemini siempre devuelve HTTP 429."""
    def invoke(self, prompt):
        error = RuntimeError("429 RESOURCE_EXHAUSTED (simulated)")
        raise error


def parse_args() -> argparse.Namespace:
    """Expone opciones para los tres escenarios de evidencia."""
    parser = argparse.ArgumentParser(description="TA-023 Explainable alerts")
    parser.add_argument("--project", type=int, default=2)
    parser.add_argument("--cutoff", default="2026-10-12T23:59:59-05:00")
    parser.add_argument("--source", choices=["fake", "dataset"], default="fake")
    parser.add_argument("--explainer", choices=["template", "gemini", "gemini-429"], default="template")
    parser.add_argument("--fail", choices=["github", "notion", "drive"])
    parser.add_argument("--evidence-dir", default="docs/sprint2/evidencias")
    parser.add_argument("--output", default="TA-023_consolidado_plantilla.json")
    return parser.parse_args()


def build_adapters(source_mode: str, failing_source: str | None) -> dict:
    """Asocia cada fuente al dataset o al adaptador simulado."""
    if source_mode == "dataset":
        adapters = {
            source: FuenteEvidenciaDataset(fuente=source)
            for source in REFERENCES
        }
    else:
        adapter = FuenteEvidenciaFalsa()
        adapters = {source: adapter for source in REFERENCES}
    if failing_source:
        adapters[failing_source] = FailingSource(failing_source)
    return adapters


def build_explainer(mode: str):
    """Devuelve plantilla, Gemini real o un 429 simulado."""
    fallback = GeneradorExplicacionPlantilla()
    if mode == "template":
        return fallback
    if mode == "gemini-429":
        primary = GeminiExplanationGenerator(FakeRateLimitLLM(), min_interval_seconds=0)
    else:
        primary = GeminiExplanationGenerator()
    return ResilientExplanationGenerator(primary, fallback)


def tracing_enabled() -> bool:
    """Evita activar trazas si la clave de LangSmith no está configurada."""
    return (
        os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        and bool(os.getenv("LANGSMITH_API_KEY", "").strip())
    )


def run_graph(args):
    """Ejecuta una instancia del grafo con nombre de traza propio."""
    explainer = build_explainer(args.explainer)
    graph = build_supervisor_graph(build_adapters(args.source, args.fail), explainer=explainer)
    initial = build_supervisor_input(args.project, args.cutoff, REFERENCES)
    config = {
        "run_name": RUN_NAME,
        "tags": ["TA-023", f"explanation-{args.explainer}"],
        "metadata": {"project_id": args.project, "cutoff": args.cutoff},
    }
    if tracing_enabled():
        project = os.getenv("LANGSMITH_PROJECT", "grupo8-sp001")
        client = Client()
        try:
            with tracing_context(enabled=True, project_name=project, client=client):
                final = graph.invoke(initial, config=config)
        finally:
            client.flush(timeout=30)
        print(f"LangSmith trace sent to project: {project}")
    else:
        with tracing_context(enabled=False):
            final = graph.invoke(initial, config=config)
        print("LangSmith tracing is disabled.")
    return final, explainer


def save_report(report: dict, evidence_dir: str, output: str) -> Path:
    """Guarda el JSON en UTF-8 dentro de la carpeta de evidencias."""
    # El nombre de salida se mantiene como archivo, no como ruta arbitraria.
    filename = Path(output).name
    target_dir = ROOT / evidence_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> None:
    args = parse_args()
    final, explainer = run_graph(args)
    report = to_consolidated_report(final)
    report["respaldos_plantilla"] = getattr(explainer, "fallbacks", [])
    target = save_report(report, args.evidence_dir, args.output)
    print(f"Output: {target.relative_to(ROOT)}")
    for source, status in report["fuentes"].items():
        print(f"{source}: {status['estado']}; evidences={status['evidencias']}; error={status['error']}")
    print(f"Indicators: {report['indicadores']}")
    for alert in report["alertas"]:
        print(
            f"{alert['regla']} {alert['fuente']} evidence={alert['evidencia_ids']} "
            f"origin={alert['origen_explicacion']}"
        )
    print(f"Fallbacks: {len(report['respaldos_plantilla'])}")


if __name__ == "__main__":
    main()
