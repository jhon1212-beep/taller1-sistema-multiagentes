"""TA-030: estabilidad de los agentes con fuentes reales.

- Un error transitorio (5xx, 429, red) se reintenta y el corte sale "ok".
- Un error permanente (credenciales, permisos) no se reintenta.
- Una fuente colgada no detiene el corte: se corta por tiempo y queda en "fallo".
- El consolidado informa intentos y duración por fuente.
- Con PostgreSQL, guardados simultáneos del mismo corte (corte.yml y el botón
  del docente) no duplican alertas: el DELETE + INSERT del repositorio ya los
  serializa por bloqueo de filas. Esta prueba lo deja comprobado.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import date

import pytest

pytest.importorskip("langgraph")

from app.modulos.evidencias.dominio import Evidencia  # noqa: E402
from app.modulos.supervision.estabilidad import (  # noqa: E402
    RetryPolicy,
    SourceTimeout,
    call_with_retry,
    is_transient,
)
from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)

CUTOFF = "2026-10-12T23:59:59-05:00"
FAST = RetryPolicy(attempts=2, backoff_s=0, timeout_s=5)


class GitHubError(Exception):
    """Mismo nombre que el error del cliente real."""


# -- clasificación ------------------------------------------------------------

@pytest.mark.parametrize("error", [
    GitHubError("HTTP 502 al consultar https://api.github.com/repos/x/y/commits"),
    GitHubError("HTTP 429 al consultar ..."),
    Exception("Error de red al consultar Notion: timed out"),
    TimeoutError("read timeout"),
    ConnectionError("Connection reset by peer"),
])
def test_errores_transitorios_se_reintentan(error):
    assert is_transient(error)


@pytest.mark.parametrize("error", [
    GitHubError("HTTP 404 al consultar ..."),
    Exception("Notion devolvió 401: token sin acceso"),
    Exception("Falta GOOGLE_SERVICE_ACCOUNT_JSON."),
    ValueError("Referencia de demostración no válida"),
    SourceTimeout("La fuente no respondió en 90 s."),
])
def test_errores_permanentes_no_se_reintentan(error):
    assert not is_transient(error)


# -- reintento y tiempo máximo ------------------------------------------------

def test_reintenta_una_vez_y_devuelve_el_resultado():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise GitHubError("HTTP 503 al consultar ...")
        return ["ok"]

    waits = []
    result, attempts = call_with_retry(flaky, RetryPolicy(attempts=2, backoff_s=1.5, timeout_s=5), waits.append)

    assert result == ["ok"] and attempts == 2
    assert waits == [1.5]


def test_error_permanente_falla_en_el_primer_intento():
    calls = []

    def denied():
        calls.append(1)
        raise GitHubError("HTTP 403 al consultar ...")

    with pytest.raises(GitHubError) as info:
        call_with_retry(denied, FAST)
    assert len(calls) == 1 and info.value.attempts == 1


def test_fuente_colgada_se_corta_por_tiempo():
    started = time.perf_counter()
    with pytest.raises(SourceTimeout):
        call_with_retry(lambda: time.sleep(3), RetryPolicy(attempts=2, backoff_s=0, timeout_s=1))
    assert time.perf_counter() - started < 2.5  # no se reintenta un tiempo agotado


def test_politica_desde_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("SUPERVISION_SOURCE_ATTEMPTS", "3")
    monkeypatch.setenv("SUPERVISION_RETRY_BACKOFF_S", "0.5")
    monkeypatch.setenv("SUPERVISION_SOURCE_TIMEOUT_S", "30")
    assert RetryPolicy.from_env() == RetryPolicy(attempts=3, backoff_s=0.5, timeout_s=30)


# -- dentro del grafo ---------------------------------------------------------

class FlakySource:
    """Falla las primeras ``failures`` llamadas con el error dado."""

    def __init__(self, source: str, error: Exception | None = None, failures: int = 0, delay: float = 0):
        self.source, self.error, self.failures, self.delay = source, error, failures, delay
        self.calls = 0

    def obtener_evidencias(self, referencia, proyecto_id, **_):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.calls <= self.failures:
            raise self.error
        return [Evidencia(proyecto_id=proyecto_id, fuente=self.source, id_externo=f"{self.source}-1",
                          autor="A", fecha="2026-10-12T10:00:00Z", descripcion="x")]


def _run(adapters, policy=FAST):
    refs = {s: f"ref-{s}" for s in adapters}
    graph = build_supervisor_graph(adapters, retry_policy=policy)
    return graph.invoke(build_supervisor_input(1, CUTOFF, refs))


def test_fallo_pasajero_de_github_ya_no_deja_la_fuente_en_fallo():
    github = FlakySource("github", GitHubError("HTTP 502 al consultar ..."), failures=1)
    final = _run({"github": github, "notion": FlakySource("notion"), "drive": FlakySource("drive")})

    assert final["estado_fuentes"] == {"github": "ok", "notion": "ok", "drive": "ok"}
    report = to_consolidated_report(final)
    assert report["estabilidad"]["github"]["intentos"] == 2
    assert report["estabilidad"]["notion"]["intentos"] == 1
    assert report["fuentes"]["github"]["evidencias"] == 1


def test_fallo_persistente_queda_en_fallo_con_sus_intentos():
    notion = FlakySource("notion", Exception("Error de red al consultar Notion: timed out"), failures=5)
    final = _run({"github": FlakySource("github"), "notion": notion})

    assert final["estado_fuentes"]["notion"] == "fallo"
    assert notion.calls == 2
    assert to_consolidated_report(final)["estabilidad"]["notion"]["intentos"] == 2
    # RN-002: la fuente caída no impide leer las demás ni genera alertas de inactividad.
    assert final["estado_fuentes"]["github"] == "ok"
    assert all(a["fuente"] != "notion" for a in final["alertas"])


def test_fuente_lenta_no_detiene_el_corte():
    slow = FlakySource("drive", delay=3)
    started = time.perf_counter()
    final = _run({"github": FlakySource("github"), "notion": FlakySource("notion"), "drive": slow},
                 RetryPolicy(attempts=2, backoff_s=0, timeout_s=1))

    assert time.perf_counter() - started < 2.8
    assert final["estado_fuentes"]["drive"] == "fallo"
    assert "no respondió" in final["errores_fuentes"]["drive"]
    assert final["estado_fuentes"]["github"] == "ok"


# -- PostgreSQL: guardados simultáneos ----------------------------------------

URL = os.getenv("DATABASE_URL", "")


def test_dos_guardados_simultaneos_no_duplican_alertas():
    if not URL:
        pytest.skip("Falta DATABASE_URL.")
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, func, select, text
    from sqlalchemy.orm import Session

    from app.compartido import modelos_orm as orm
    from app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository
    from app.modulos.supervision.service import SupervisionService
    from app.modulos.supervision.sources import build_explainer, build_source_adapters

    engine = create_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1 from indicador limit 1"))
    except Exception as error:
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")

    refs = {"github": "dataset:1", "notion": "dataset:1", "drive": "dataset:1"}
    with Session(engine) as s:
        teacher = orm.Docente(nombre="Docente TA-030", correo="ta030@prueba.test", password_hash="x")
        s.add(teacher)
        s.flush()
        project = orm.Proyecto(docente_id=teacher.id, nombre="Proyecto TA-030", curso="TI1",
                               fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
                               url_publica="https://demo.test", elemento_verificar="h1")
        s.add(project)
        s.flush()
        for kind, ref in refs.items():
            s.add(orm.Fuente(proyecto_id=project.id, tipo=kind, referencia=ref))
        s.commit()
        project_id, teacher_id = project.id, teacher.id

    errors = []

    def cut():
        try:
            with Session(engine) as s:
                SupervisionService(SqlSupervisionRepository(s), build_source_adapters("dataset"),
                                   build_explainer("template")).run_cutoff(project_id, refs, CUTOFF)
        except Exception as error:  # pragma: no cover - se informa abajo
            errors.append(error)

    try:
        once = threading.Thread(target=cut)
        once.start()
        once.join()
        with Session(engine) as s:
            expected = s.scalar(select(func.count()).select_from(orm.Alerta)
                                .where(orm.Alerta.proyecto_id == project_id))

        threads = [threading.Thread(target=cut) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        with Session(engine) as s:
            total = s.scalar(select(func.count()).select_from(orm.Alerta)
                             .where(orm.Alerta.proyecto_id == project_id))
        assert expected > 0 and total == expected
    finally:
        with Session(engine) as s:
            s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == project_id))
            s.delete(s.get(orm.Proyecto, project_id))
            s.flush()
            s.delete(s.get(orm.Docente, teacher_id))
            s.commit()
