"""Semana 10 (TA-018, TA-022, TA-037): métricas de viabilidad del Supervisor.

Mide, con el proyecto demo de TA-017 y sin costo:
  A. Exactitud del motor frente a los valores esperados del dataset.
  B. Tiempo del grafo y ganancia del paralelismo (Send) frente a un recorrido secuencial.
  C. Resiliencia: el corte termina aunque falle una fuente.
  D. Privacidad: nombres reales que llegarían a Gemini (debe ser 0).
  E. Tiempos de la API (10 peticiones por ruta): local con PostgreSQL o en Render.
  F. Costo y consumo de cuota de Gemini por corte.

Uso seguro desde la raíz del repositorio:
    python backend/scripts/measure_supervision_metrics.py --no-api
Para medir peticiones, confirmar primero la rama aislada de Neon y ejecutar
con --allow-test-db-writes. El modo remoto solicita la clave sin mostrarla.
Escribe docs/sprint2/evidencias/TA-022_metricas.json y TA-022_metricas.md.
"""
from __future__ import annotations

import argparse
import getpass
import secrets
import uuid
from sqlalchemy.engine import make_url
import json
import statistics
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402
from app.modulos.supervision.adaptadores.gemini import build_explanation_prompt  # noqa: E402
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla  # noqa: E402
from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.pseudonymizer import Pseudonymizer  # noqa: E402
from app.modulos.supervision.sources import build_source_adapters  # noqa: E402

CUTOFF = "2026-10-12T23:59:59-05:00"  # fecha de corte del dataset TA-017
OUT_DIR = ROOT / "docs" / "sprint2" / "evidencias"
SOURCES = ("github", "notion", "drive")


def stats_ms(samples: list[float]) -> dict[str, float]:
    """Resumen de una lista de tiempos en milisegundos."""
    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))]
    return {
        "n": len(samples),
        "media": round(statistics.mean(samples), 1),
        "desv_est": round(statistics.stdev(samples), 1) if len(samples) > 1 else 0.0,
        "min": round(ordered[0], 1),
        "p50": round(statistics.median(samples), 1),
        "p95": round(p95, 1),
        "max": round(ordered[-1], 1),
    }


def refs(project: int) -> dict[str, str]:
    return {source: f"dataset:{project}" for source in SOURCES}


def run_graph(adapters, project: int) -> dict:
    graph = build_supervisor_graph(adapters, explainer=GeneradorExplicacionPlantilla())
    return graph.invoke(build_supervisor_input(project, CUTOFF, refs(project)))


# -- A. Exactitud --------------------------------------------------------------
def accuracy() -> dict:
    data = cargar_dataset()
    result = {}
    for project in (1, 2):
        final = run_graph(build_source_adapters("dataset"), project)
        got = {(a["regla"], a["evidencia_ids"][0] if a["evidencia_ids"] else None)
               for a in final["alertas"]}
        expected = {(a["regla"], a["evidencia_id"]) for a in data["alertas_esperadas"][str(project)]}
        hits = len(got & expected)
        ind_got, ind_exp = final["indicadores"], data["indicadores_esperados"][str(project)]
        result[f"proyecto_{project}"] = {
            "alertas_esperadas": len(expected),
            "alertas_obtenidas": len(got),
            "precision_pct": round(100 * hits / len(got), 1) if got else 100.0,
            "exhaustividad_pct": round(100 * hits / len(expected), 1) if expected else 100.0,
            "indicadores_coinciden": sum(ind_got[k] == ind_exp[k] for k in ind_exp),
            "indicadores_total": len(ind_exp),
            "diferencias": {k: {"obtenido": ind_got[k], "json_ta017": ind_exp[k]}
                            for k in ind_exp if ind_got[k] != ind_exp[k]},
        }
    return result


# -- B. Tiempo del grafo y paralelismo ---------------------------------------
class DelayedSource:
    """Simula la latencia de red de una API real (p. ej. 300 ms por consulta)."""

    def __init__(self, inner, delay_s: float) -> None:
        self._inner, self._delay = inner, delay_s

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        time.sleep(self._delay)
        return self._inner.obtener_evidencias(referencia, proyecto_id, limite=limite, desde=desde)


def graph_timing(runs: int, delay_s: float) -> dict:
    base = build_source_adapters("dataset")
    plain = [run_graph_timed(base, 1) for _ in range(runs)]

    delayed = {s: DelayedSource(a, delay_s) for s, a in base.items()}
    parallel = [run_graph_timed(delayed, 1) for _ in range(5)]
    sequential = []
    for _ in range(5):  # mismo trabajo, una fuente tras otra (como el grafo de TA-012)
        started = time.perf_counter()
        for source, adapter in delayed.items():
            adapter.obtener_evidencias(f"dataset:1", 1)
        sequential.append((time.perf_counter() - started) * 1000)
    par, seq = statistics.mean(parallel), statistics.mean(sequential)
    return {
        "grafo_sin_latencia_ms": stats_ms(plain),
        "latencia_simulada_por_fuente_ms": delay_s * 1000,
        "lectura_paralela_ms": stats_ms(parallel),
        "lectura_secuencial_ms": stats_ms(sequential),
        "aceleracion_paralelo": round(seq / par, 2),
        "nota_comparabilidad": (
            "Comparación exploratoria: paralelo incluye todo el grafo; "
            "secuencial solo mide consultas a fuentes. No prueba speedup exacto."
        ),
    }


def run_graph_timed(adapters, project: int) -> float:
    started = time.perf_counter()
    run_graph(adapters, project)
    return (time.perf_counter() - started) * 1000


# -- C. Resiliencia -------------------------------------------------------------
class FailingSource:
    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        raise ConnectionError("fuente no disponible (simulado)")


def resilience() -> dict:
    scenarios = {}
    for failing in SOURCES:
        adapters = dict(build_source_adapters("dataset"))
        adapters[failing] = FailingSource()
        report = to_consolidated_report(run_graph(adapters, 2))
        scenarios[failing] = {
            "corte_completado": True,
            "fuentes_ok": sum(v["estado"] == "ok" for v in report["fuentes"].values()),
            "fuente_marcada_fallo": report["fuentes"][failing]["estado"] == "fallo",
            "alertas_falsas_de_la_fuente_caida": sum(a["fuente"] == failing for a in report["alertas"]),
        }
    return {"escenarios": scenarios,
            "cortes_completados": f"{len(scenarios)}/{len(SOURCES)}"}


# -- D. Privacidad --------------------------------------------------------------
def privacy() -> dict:
    prompts, leaks = 0, 0
    for project in (1, 2):
        final = run_graph(build_source_adapters("dataset"), project)
        evidences = final["evidencias"]
        names = {e.autor for e in evidences if e.autor and e.autor not in ("desconocido",)}
        pseudo = Pseudonymizer.from_evidences(evidences)
        for alert in final["alertas"]:
            prompt = build_explanation_prompt(alert, CUTOFF, pseudo.alert_context(alert, evidences))
            prompts += 1
            leaks += sum(1 for name in names if name in prompt)
    return {"prompts_revisados": prompts, "nombres_reales_en_prompts": leaks}


# -- E. API ---------------------------------------------------------------------
def api_local(requests_per_route: int) -> dict:
    """API en proceso contra PostgreSQL (DATABASE_URL); crea y borra datos de prueba."""
    import os

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.compartido import modelos_orm as orm
    from app.main import app
    from app.modulos.autenticacion.servicio import hashear_password

    os.environ.setdefault("JWT_SECRET", "m" * 40)  # solo si el .env no lo trae
    os.environ["SUPERVISION_SOURCES"] = "dataset"
    os.environ["SUPERVISION_EXPLAINER"] = "template"
    engine = create_engine(os.environ["DATABASE_URL"])
    password = secrets.token_urlsafe(18)
    email = f"metricas-{uuid.uuid4().hex[:12]}@prueba.test"
    with Session(engine) as s:
        teacher = orm.Docente(nombre="Docente métricas", correo=email,
                              password_hash=hashear_password(password, rondas=4))
        s.add(teacher)
        s.flush()
        project = orm.Proyecto(docente_id=teacher.id, nombre="Demo métricas", curso="TI1",
                               fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
                               url_publica="https://demo.test", elemento_verificar="h1")
        s.add(project)
        s.flush()
        for source in SOURCES:
            s.add(orm.Fuente(proyecto_id=project.id, tipo=source, referencia="dataset:1"))
        s.commit()
        teacher_id, project_id = teacher.id, project.id
    try:
        client = TestClient(app)
        login = client.post("/auth/login", json={"correo": email, "password": password})
        if login.status_code != 200:
            raise RuntimeError(f"No se pudo iniciar sesión para medir: HTTP {login.status_code}")
        token = login.json()["token"]
        return measure_routes(client, {"Authorization": f"Bearer {token}"}, project_id,
                              requests_per_route, "local (TestClient + PostgreSQL 16)")
    finally:
        with Session(engine) as s:
            s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == project_id))
            s.delete(s.get(orm.Proyecto, project_id))
            s.flush()
            s.delete(s.get(orm.Docente, teacher_id))
            s.commit()


def api_remote(base_url: str, email: str, password: str, project_id: int, n: int) -> dict:
    import httpx

    with httpx.Client(base_url=base_url, timeout=60) as client:
        login = client.post("/auth/login", json={"correo": email, "password": password})
        if login.status_code != 200:
            raise RuntimeError(f"No se pudo iniciar sesión: HTTP {login.status_code}")
        token = login.json()["token"]
        return measure_routes(client, {"Authorization": f"Bearer {token}"}, project_id, n, base_url)


def measure_routes(client, headers, project_id: int, n: int, where: str) -> dict:
    cuts = ("2026-10-06T23:59:59-05:00", CUTOFF)
    for cut in cuts:  # datos de ensayo; cada POST reescribe el corte del mismo día
        response = client.post(
            f"/proyectos/{project_id}/consolidacion",
            json={"fecha_corte": cut}, headers=headers,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Preparación del corte {cut}: HTTP {response.status_code}")
    routes = {
        "POST /consolidacion": lambda: client.post(f"/proyectos/{project_id}/consolidacion",
                                                  json={"fecha_corte": CUTOFF}, headers=headers),
        "GET /indicadores": lambda: client.get(f"/proyectos/{project_id}/indicadores", headers=headers),
        "GET /alertas": lambda: client.get(f"/proyectos/{project_id}/alertas", headers=headers),
        "GET /historial": lambda: client.get(f"/proyectos/{project_id}/historial", headers=headers),
    }
    result = {"entorno": where, "peticiones_por_ruta": n, "rutas": {}}
    for name, call in routes.items():
        samples, errors, statuses = [], 0, []
        desglose_post = []
        for _ in range(n):
            started = time.perf_counter()
            try:
                response = call()
                status = response.status_code
            except Exception as exc:
                status = f"EXCEPTION:{type(exc).__name__}"
            elapsed = (time.perf_counter() - started) * 1000
            if name == "POST /consolidacion" and status == 200:
                body = response.json()
                desglose_post.append({
                    "http_ms": round(elapsed, 1),
                    "grafo_ms": body.get("duracion_grafo_ms"),
                    "sql_ms": body.get("duracion_sql_ms"),
                    "servicio_ms": body.get("duracion_servicio_ms"),
                })
            samples.append(elapsed)
            statuses.append(status)
            errors += status != 200
        result["rutas"][name] = {
            **stats_ms(samples),
            "errores": errors,
            "codigos_http": statuses,
            "muestras_ms": [round(x, 1) for x in samples],
            "cumple_menos_de_2s": errors == 0 and max(samples) < 2000,
        }
        if name == "POST /consolidacion":
            result["rutas"][name]["desglose_post"] = desglose_post
    history = client.get(f"/proyectos/{project_id}/historial", headers=headers).json()
    result["cortes_en_historial"] = history["total_cortes"]
    return result


# -- F. Costo y cuota -------------------------------------------------------------
def cost() -> dict:
    alerts = {p: len(run_graph(build_source_adapters("dataset"), p)["alertas"]) for p in (1, 2)}
    return {
        "costo_servicios_soles": 0,
        "llamadas_gemini_por_corte_hoy": alerts,  # una por alerta (TA-023)
        "limite_diario_gratuito_gemini": 20,
        "nota": (
            "Estimación del documento base, no consumo real ni cuota verificada. "
            "Este ensayo utiliza template y no invoca Gemini."
        ),
    }


def to_markdown(m: dict) -> str:
    lines = [f"# Métricas de viabilidad · semana 10 · {m['generado_en']}", ""]
    lines += ["## A. Exactitud del motor (dataset TA-017)", "",
              "| Proyecto | Alertas esperadas | Obtenidas | Precisión | Exhaustividad | Indicadores iguales al JSON |",
              "|---|---|---|---|---|---|"]
    for p, v in m["exactitud"].items():
        lines.append(f"| {p} | {v['alertas_esperadas']} | {v['alertas_obtenidas']} | {v['precision_pct']} % | "
                     f"{v['exhaustividad_pct']} % | {v['indicadores_coinciden']}/{v['indicadores_total']} |")
    t = m["tiempos_grafo"]
    lines += ["", "## B. Tiempo del grafo", "",
              f"- Grafo completo sin latencia: media {t['grafo_sin_latencia_ms']['media']} ms, "
              f"p95 {t['grafo_sin_latencia_ms']['p95']} ms (n={t['grafo_sin_latencia_ms']['n']}).",
              f"- Con {t['latencia_simulada_por_fuente_ms']:.0f} ms por fuente: paralelo "
              f"{t['lectura_paralela_ms']['media']} ms frente a secuencial {t['lectura_secuencial_ms']['media']} ms "
              f"(x{t['aceleracion_paralelo']})."]
    lines += ["", "## C. Resiliencia", "", f"Cortes completados con una fuente caída: {m['resiliencia']['cortes_completados']}."]
    lines += ["", "## D. Privacidad", "",
              f"{m['privacidad']['nombres_reales_en_prompts']} nombres reales en {m['privacidad']['prompts_revisados']} prompts."]
    if m.get("api"):
        lines += ["", f"## E. API ({m['api']['entorno']}, {m['api']['peticiones_por_ruta']} peticiones por ruta)", "",
                  "| Ruta | Media (ms) | p50 | p95 | Máx. | Errores | < 2 s |", "|---|---|---|---|---|---|---|"]
        for route, v in m["api"]["rutas"].items():
            lines.append(f"| {route} | {v['media']} | {v['p50']} | {v['p95']} | {v['max']} | {v['errores']} | "
                         f"{'Sí' if v['cumple_menos_de_2s'] else 'No'} |")
    lines += ["", "## F. Costo", "", f"S/ {m['costo']['costo_servicios_soles']} · llamadas a Gemini por corte: "
              f"{m['costo']['llamadas_gemini_por_corte_hoy']} (límite gratuito {m['costo']['limite_diario_gratuito_gemini']}/día)."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url")
    parser.add_argument("--email")
    # No introducir contraseñas como argumento: quedan en el historial del shell.
    parser.add_argument("--project-id", type=int)
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--graph-runs", type=int, default=30)
    parser.add_argument("--delay", type=float, default=0.3, help="latencia simulada por fuente (s)")
    parser.add_argument("--no-api", action="store_true")
    parser.add_argument(
        "--allow-test-db-writes", action="store_true",
        help="Confirmación explícita: se escribirán cortes en la base de prueba",
    )
    parser.add_argument(
        "--expected-db-host",
        help="Host exacto del endpoint aislado de Neon (obligatorio en modo local)",
    )
    args = parser.parse_args()
    if args.graph_runs < 1 or args.requests < 1:
        parser.error("--requests y --graph-runs deben ser mayores que cero")
    if not args.no_api:
        if not args.allow_test_db_writes:
            parser.error("Para medir API que guarda cortes, añade --allow-test-db-writes")
        if args.base_url:
            if not args.email or args.project_id is None:
                parser.error("Con --base-url debes indicar --email y --project-id")
        else:
            from app.compartido.config import obtener_database_url
            real_host = make_url(obtener_database_url()).host
            if not args.expected_db_host or args.expected_db_host != real_host:
                parser.error(
                    "Host de PostgreSQL no confirmado. Compara con tu rama Neon "
                    "y pasa --expected-db-host con el valor exacto."
                )

    metrics = {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exactitud": accuracy(),
        "tiempos_grafo": graph_timing(args.graph_runs, args.delay),
        "resiliencia": resilience(),
        "privacidad": privacy(),
        "costo": cost(),
    }
    if not args.no_api:
        if args.base_url:
            password = getpass.getpass("Contraseña del docente demo (no se muestra): ")
            metrics["api"] = api_remote(args.base_url, args.email, password,
                                        args.project_id, args.requests)
        else:
            metrics["api"] = api_local(args.requests)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "TA-022_metricas.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    (OUT_DIR / "TA-022_metricas.md").write_text(to_markdown(metrics), encoding="utf-8")
    print(to_markdown(metrics))


if __name__ == "__main__":
    main()