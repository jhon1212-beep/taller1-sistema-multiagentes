"""TA-037: CP-10 del Supervisor con dataset y fuentes externas reales.

Criterios: consolidado con GitHub, Notion y Drive en estado ``ok``, y
traza completa en LangSmith (verificación visual independiente).

La prueba de dataset siempre se ejecuta. La prueba real se omite si faltan
las credenciales o las referencias configuradas para las tres fuentes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Cargar el .env del repositorio antes de determinar qué pruebas se omiten.
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from app.modulos.supervision.adaptadores.plantilla import (  # noqa: E402
    GeneradorExplicacionPlantilla,
)
from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.sources import build_source_adapters  # noqa: E402

EVIDENCE = ROOT / "docs" / "sprint2" / "evidencias" / "TA-037_cp10_consolidado.json"
# En .env.example, CP10_CUTOFF puede existir pero estar vacío.
CUTOFF = os.getenv("CP10_CUTOFF", "").strip() or "2026-11-04T23:59:59-05:00"
REQUIRED = (
    "GITHUB_TOKEN",
    "CP10_GITHUB_REPO",
    "NOTION_TOKEN",
    "NOTION_DATABASE_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_DRIVE_FOLDER_ID",
)
MISSING = tuple(name for name in REQUIRED if not os.getenv(name, "").strip())


def assert_cp10(report: dict) -> None:
    """Aplicar los mismos criterios de aceptación a dataset y fuentes reales."""
    states = {source: data["estado"] for source, data in report["fuentes"].items()}
    assert states == {"github": "ok", "notion": "ok", "drive": "ok"}, report["fuentes"]
    for source, data in report["fuentes"].items():
        assert data["evidencias"] > 0, f"{source} no trajo evidencias"
        assert data["error"] is None
    assert report["total_evidencias"] == sum(
        data["evidencias"] for data in report["fuentes"].values()
    )
    assert set(report["indicadores"]) == {"I1", "I2", "I3", "I4"}
    assert all(alert["explicacion"] for alert in report["alertas"])


def test_cp10_check_with_demo_dataset() -> None:
    graph = build_supervisor_graph(
        build_source_adapters("dataset"),
        explainer=GeneradorExplicacionPlantilla(),
    )
    refs = {"github": "dataset:1", "notion": "dataset:1", "drive": "dataset:1"}
    final = graph.invoke(
        build_supervisor_input(1, "2026-10-12T23:59:59-05:00", refs)
    )
    assert_cp10(to_consolidated_report(final))


@pytest.mark.skipif(
    bool(MISSING),
    reason="CP-10 real: faltan variables en .env: " + ", ".join(MISSING),
)
def test_cp10_with_real_sources() -> None:
    refs = {
        "github": os.environ["CP10_GITHUB_REPO"],
        "notion": os.environ["NOTION_DATABASE_ID"],
        "drive": os.environ["GOOGLE_DRIVE_FOLDER_ID"],
    }
    graph = build_supervisor_graph(
        build_source_adapters("real"),
        explainer=GeneradorExplicacionPlantilla(),
    )
    config = {
        "run_name": "TA-037 CP-10 real sources",
        "tags": ["TA-037", "CP-10"],
        "metadata": {"cutoff": CUTOFF},
    }
    final = graph.invoke(build_supervisor_input(1, CUTOFF, refs), config=config)
    report = to_consolidated_report(final)

    # Dejar evidencia de diagnóstico: excluye el detalle de cada evidencia.
    # Revisar este JSON por privacidad antes de subirlo a Git.
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    summary = {key: value for key, value in report.items() if key != "evidencias"}
    EVIDENCE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    assert_cp10(report)
