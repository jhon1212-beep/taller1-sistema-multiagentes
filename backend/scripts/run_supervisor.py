"""TA-015: ejecuta el Agente Supervisor y guarda el consolidado como evidencia.

Uso (desde la raíz del repositorio):

    python backend/scripts/run_supervisor.py
    python backend/scripts/run_supervisor.py --github real --repo owner/repo
    python backend/scripts/run_supervisor.py --fail notion --output TA-015_consolidado_fallo.json

Notion y Drive usan FuenteEvidenciaFalsa hasta que existan sus agentes reales
(TA-007 y TA-014). GitHub puede usar el adaptador real de TA-006 si el .env
tiene GITHUB_TOKEN.

Si LANGSMITH_TRACING=true y LANGSMITH_API_KEY están en el .env, la ejecución
queda trazada en LangSmith.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# Bloque 1. Rutas y variables de entorno

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

# Permite importar el paquete app al ejecutar el script desde la raíz.
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Lee el .env local; las claves nunca se escriben en el código.
load_dotenv(ROOT / ".env")

from langsmith import Client, tracing_context  # noqa: E402

from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa  # noqa: E402
from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)

EVIDENCE_DIR = ROOT / "docs" / "sprint1" / "evidencias"
RUN_NAME = "TA-015 Agente Supervisor"


# Bloque 2. Adaptador que simula una fuente caída

class FailingSource:
    """Adaptador que siempre falla; sirve para la evidencia de una fuente caída."""

    def __init__(self, source: str) -> None:
        self.source = source

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        # Respeta la firma del puerto FuenteEvidencia (AR-01), pero siempre falla.
        raise ConnectionError(f"{self.source} no responde (fallo simulado)")


# Bloque 3. Selección de adaptadores por fuente

def build_adapters(github_mode: str, fail: str | None) -> dict:
    """Arma un adaptador por fuente según las opciones de la línea de comandos."""
    fake = FuenteEvidenciaFalsa()
    adapters = {"github": fake, "notion": fake, "drive": fake}

    if github_mode == "real":
        # Import local: solo se necesita el cliente de GitHub en modo real.
        from app.modulos.evidencias.adaptadores.github.adaptador import (
            FuenteEvidenciaGitHub,
        )

        adapters["github"] = FuenteEvidenciaGitHub()

    if fail:
        adapters[fail] = FailingSource(fail)

    return adapters


# Bloque 4. ¿Hay traza en LangSmith?

def tracing_enabled() -> bool:
    """La traza solo se activa si el .env tiene LANGSMITH_TRACING y la clave."""
    return (
        os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        and bool(os.getenv("LANGSMITH_API_KEY", "").strip())
    )


# Bloque 5. Opciones de la línea de comandos

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TA-015 · Agente Supervisor")
    parser.add_argument("--project", type=int, default=1)
    parser.add_argument("--cutoff", default="2026-10-12T23:59:59-05:00")
    parser.add_argument("--github", choices=["fake", "real"], default="fake")
    parser.add_argument("--repo", default="repositorio-demo")
    parser.add_argument("--notion", default="base-demo")
    parser.add_argument("--drive", default="carpeta-demo")
    parser.add_argument("--fail", choices=["github", "notion", "drive"])
    parser.add_argument("--output", default="TA-015_consolidado.json")
    return parser.parse_args()


# Bloque 6. Ejecución del grafo (con o sin traza)

def run_graph(args: argparse.Namespace) -> tuple[dict, str]:
    graph = build_supervisor_graph(build_adapters(args.github, args.fail))
    initial = build_supervisor_input(
        args.project,
        args.cutoff,
        {"github": args.repo, "notion": args.notion, "drive": args.drive},
    )

    # Nombre, etiquetas y metadatos con los que la ejecución aparece en LangSmith.
    config = {
        "run_name": RUN_NAME,
        "tags": ["TA-015", f"github-{args.github}"]
        + ([f"fallo-{args.fail}"] if args.fail else []),
        "metadata": {"proyecto_id": args.project, "fecha_corte": args.cutoff},
    }

    if tracing_enabled():
        project = os.getenv("LANGSMITH_PROJECT", "grupo8-sp001")
        client = Client()
        try:
            with tracing_context(enabled=True, project_name=project, client=client):
                final = graph.invoke(initial, config=config)
        finally:
            # Asegura que la traza se envíe antes de que termine el proceso.
            client.flush(timeout=30)
        note = f"Traza enviada a LangSmith · proyecto '{project}' · ejecución '{RUN_NAME}'."
    else:
        with tracing_context(enabled=False):
            final = graph.invoke(initial, config=config)
        note = (
            "Sin traza: configura LANGSMITH_TRACING=true y LANGSMITH_API_KEY "
            "en el .env para cumplir el criterio 3."
        )

    return final, note


# Bloque 7. Guardar el consolidado y mostrar el resumen

def save_report(report: dict, output: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    target = EVIDENCE_DIR / output
    text = json.dumps(report, ensure_ascii=False, indent=2)
    target.write_text(text + "\n", encoding="utf-8")
    print(text)
    return target


def print_summary(report: dict) -> None:
    print()
    for source, data in report["fuentes"].items():
        print(
            f"  {source:<7} {data['estado']:<6} evidencias={data['evidencias']}  "
            f"fuera_de_corte={data['fuera_de_corte']}  error={data['error']}"
        )


def main() -> None:
    args = parse_args()
    final, note = run_graph(args)
    report = to_consolidated_report(final)
    target = save_report(report, args.output)
    print_summary(report)
    print(f"\nConsolidado guardado en: {target.relative_to(ROOT)}")
    print(note)


if __name__ == "__main__":
    main()