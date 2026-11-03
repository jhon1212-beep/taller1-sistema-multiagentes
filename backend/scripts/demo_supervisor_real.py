"""TA-012: demo del grafo con fuente falsa y traza en LangSmith."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

load_dotenv(RAIZ / ".env")

from langsmith import Client, tracing_context  # noqa: E402
from app.main import crear_fuente_evidencias
from app.modulos.evidencias.adaptadores.falso import (  # noqa: E402
    FuenteEvidenciaFalsa,
)
from app.modulos.supervision.grafo.construir_grafo import (  # noqa: E402
    construir_grafo,
)
from app.modulos.supervision.grafo.estado import (  # noqa: E402
    crear_estado_inicial,
)


def main() -> None:
    if os.getenv("LANGSMITH_TRACING", "").lower() != "true":
        raise SystemExit(
            "Configura LANGSMITH_TRACING=true en el .env."
        )

    if not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise SystemExit(
            "Configura LANGSMITH_API_KEY en el .env."
        )

    proyecto_langsmith = os.getenv(
        "LANGSMITH_PROJECT",
        "grupo8-sp001",
    )

    referencias = {
    "github": os.getenv("REPO_DEMO", "").strip(),
    "notion": os.getenv("NOTION_DATABASE_ID", "").strip(),
    "drive": os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip(),
    }
    faltantes = [nombre for nombre, valor in referencias.items() if not valor]
    if faltantes:
        raise SystemExit("Faltan en el .env: " + ", ".join(faltantes))

    grafo = construir_grafo(
        crear_fuente_evidencias(referencias),
        referencias,
    )
    inicial = crear_estado_inicial(
        1,
        "2026-10-06T00:00:00Z",
    )

    cliente = Client()

    try:
        with tracing_context(
            enabled=True,
            project_name=proyecto_langsmith,
            client=cliente,
        ):
            resultado = grafo.invoke(
                inicial,
                config={
                    "run_name": "TA-036 supervisor con fuentes reales",
                    "tags": ["TA-036", "fuentes-reales"],
                    "metadata": {"proyecto_id": 1},
                },
            )
    finally:
        cliente.flush(timeout=30)

    consolidado = {
        **resultado,
        "evidencias": [
            evidencia.to_dict()
            for evidencia in resultado["evidencias"]
        ],
    }

    destino = (
        RAIZ / "docs" / "sprint2" / "evidencias"
        / "TA-036_consolidado_real.json"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)

    texto = json.dumps(
        consolidado,
        ensure_ascii=False,
        indent=2,
    )
    destino.write_text(texto + "\n", encoding="utf-8")

    print(texto)
    print(f"\nConsolidado guardado en: {destino}")
    print(f"Proyecto LangSmith: {proyecto_langsmith}")
    print("Ejecucion: TA-036 supervisor con fuentes reales")
    print("Comprueba la traza en LangSmith.")


if __name__ == "__main__":
    main()