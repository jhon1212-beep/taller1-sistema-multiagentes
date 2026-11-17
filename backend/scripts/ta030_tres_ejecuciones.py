"""TA-030: 3 ejecuciones del Supervisor con fuentes reales y su traza en LangSmith.

Mide, por ejecución, el estado de cada fuente, los intentos que necesitó
(reintentos de TA-030), la duración por agente, las evidencias leídas y el
origen de las explicaciones. No usa la base de datos: corre el grafo directo.

Uso (desde la raíz del repositorio, con el .env completo):

    python backend/scripts/ta030_tres_ejecuciones.py \
        --github https://github.com/org/repo \
        --notion https://www.notion.so/<id-de-la-base> \
        [--drive https://drive.google.com/drive/folders/<id>]   # opcional

Sin argumentos usa REPO_DEMO, NOTION_DATABASE_ID y GOOGLE_DRIVE_FOLDER_ID del .env.
Escribe docs/sprint2/evidencias/TA-030_ejecuciones.json y .md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
load_dotenv(RAIZ / ".env")

from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.sources import build_explainer, build_source_adapters  # noqa: E402

DESTINO = RAIZ / "docs" / "sprint2" / "evidencias"


def _argumentos() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--github", default=os.getenv("REPO_DEMO", ""))
    p.add_argument("--notion", default=os.getenv("NOTION_DATABASE_ID", ""))
    p.add_argument("--drive", default=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""), help="opcional")
    p.add_argument("--ejecuciones", type=int, default=3)
    p.add_argument("--pausa", type=float, default=5.0, help="segundos entre ejecuciones")
    p.add_argument("--corte", default=None, help="ISO 8601 con zona; por defecto, fin del día de hoy en Lima")
    return p.parse_args()


def _corte_de_hoy() -> str:
    return f"{datetime.now(ZoneInfo('America/Lima')).date().isoformat()}T23:59:59-05:00"


def _una_ejecucion(graph, referencias: dict, corte: str, numero: int) -> dict:
    inicio = time.perf_counter()
    final = graph.invoke(
        build_supervisor_input(1, corte, referencias),
        config={
            "run_name": f"TA-030 ejecución {numero}",
            "tags": ["TA-030", "fuentes-reales", f"ejecucion-{numero}"],
            "metadata": {"ejecucion": numero, "corte": corte, "fuentes": sorted(referencias)},
        },
    )
    total_ms = round((time.perf_counter() - inicio) * 1000, 1)
    reporte = to_consolidated_report(final)
    return {
        "ejecucion": numero,
        "inicio": datetime.now(ZoneInfo("America/Lima")).isoformat(timespec="seconds"),
        "duracion_total_ms": total_ms,
        "fuentes": reporte["fuentes"],
        "estabilidad": reporte["estabilidad"],
        "total_evidencias": reporte["total_evidencias"],
        "indicadores": reporte["indicadores"],
        "alertas_por_regla": dict(sorted(Counter(a["regla"] for a in reporte["alertas"]).items())),
        "origen_explicaciones": dict(Counter(a["origen_explicacion"] for a in reporte["alertas"])),
    }


def _tabla(ejecuciones: list[dict]) -> str:
    filas = ["| # | Duración total | GitHub | Notion | Drive | Evidencias | Alertas | Explicaciones |",
             "|---|---|---|---|---|---|---|---|"]
    for e in ejecuciones:
        def celda(f: str) -> str:
            fuente, est = e["fuentes"][f], e["estabilidad"].get(f)
            if fuente["estado"] == "no_configurada":
                return "no configurada"
            extra = f", {est['intentos']} int., {est['duracion_ms']:.0f} ms" if est else ""
            return f"{fuente['estado']} ({fuente['evidencias']}{extra})"
        filas.append(
            f"| {e['ejecucion']} | {e['duracion_total_ms']:.0f} ms | {celda('github')} | {celda('notion')} | "
            f"{celda('drive')} | {e['total_evidencias']} | {e['alertas_por_regla'] or '—'} | "
            f"{e['origen_explicaciones'] or '—'} |"
        )
    return "\n".join(filas)


def main() -> None:
    args = _argumentos()
    referencias = {k: v.strip() for k, v in {"github": args.github, "notion": args.notion,
                                               "drive": args.drive}.items() if v and v.strip()}
    faltan = [f for f in ("github", "notion") if f not in referencias]
    if faltan:
        raise SystemExit("Faltan referencias obligatorias: " + ", ".join(faltan))
    if os.getenv("LANGSMITH_TRACING", "").lower() != "true" or not os.getenv("LANGSMITH_API_KEY"):
        print("Aviso: LANGSMITH_TRACING/LANGSMITH_API_KEY no están configurados; no habrá trazas.")

    graph = build_supervisor_graph(build_source_adapters("real"), explainer=build_explainer())
    corte = args.corte or _corte_de_hoy()
    ejecuciones = []
    for numero in range(1, args.ejecuciones + 1):
        print(f"Ejecución {numero}/{args.ejecuciones}…", flush=True)
        ejecuciones.append(_una_ejecucion(graph, referencias, corte, numero))
        if numero < args.ejecuciones:
            time.sleep(args.pausa)

    resultado = {
        "corte": corte,
        "fuentes_registradas": sorted(referencias),
        "proyecto_langsmith": os.getenv("LANGSMITH_PROJECT", "grupo8-sp001"),
        "explicador": os.getenv("SUPERVISION_EXPLAINER", "template"),
        "politica": {
            "intentos": os.getenv("SUPERVISION_SOURCE_ATTEMPTS", "2"),
            "espera_s": os.getenv("SUPERVISION_RETRY_BACKOFF_S", "2"),
            "tiempo_maximo_s": os.getenv("SUPERVISION_SOURCE_TIMEOUT_S", "90"),
        },
        "ejecuciones": ejecuciones,
    }
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "TA-030_ejecuciones.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tabla = _tabla(ejecuciones)
    (DESTINO / "TA-030_ejecuciones.md").write_text(
        f"# TA-030 · 3 ejecuciones con fuentes reales\n\nCorte: {corte} · "
        f"Fuentes: {', '.join(resultado['fuentes_registradas'])} · "
        f"Proyecto LangSmith: {resultado['proyecto_langsmith']} (tag `TA-030`)\n\n{tabla}\n",
        encoding="utf-8")
    print("\n" + tabla)
    print(f"\nGuardado en {DESTINO / 'TA-030_ejecuciones.json'} y .md")


if __name__ == "__main__":
    main()
