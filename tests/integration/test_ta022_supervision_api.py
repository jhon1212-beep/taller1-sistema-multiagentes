"""TA-022: API de consulta consolidada (consolidación, indicadores, alertas e historial).

Criterios: 1) las 4 rutas existen; 2) cada una responde en menos de 2 s en
10 peticiones (aquí en local; en Render se mide con
scripts/measure_supervision_metrics.py); 3) pytest en verde.
Usa PostgreSQL real y el login real de HU-001 (bcrypt + JWT).
"""
import os
import time
from datetime import date

import pytest

pytest.importorskip("sqlalchemy")
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido import modelos_orm as orm  # noqa: E402
from app.main import app  # noqa: E402
from app.modulos.autenticacion.servicio import hashear_password  # noqa: E402
from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402

URL = os.getenv("DATABASE_URL", "")
PASSWORD = "ClaveDePrueba-2026"  # solo para la base de pruebas
CUTS = ("2026-10-06T23:59:59-05:00", "2026-10-12T23:59:59-05:00")
MAX_SECONDS = 2.0
REQUESTS = 10


@pytest.fixture
def api(monkeypatch):
    if not URL:
        pytest.skip("Falta DATABASE_URL.")
    engine = create_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1 from indicador limit 1"))
    except Exception as error:
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")
    monkeypatch.setenv("JWT_SECRET", "s" * 40)  # secreto de prueba
    monkeypatch.setenv("SUPERVISION_SOURCES", "dataset")
    monkeypatch.setenv("SUPERVISION_EXPLAINER", "template")

    with Session(engine) as s:
        owner = orm.Docente(nombre="Docente TA-022", correo="ta022@prueba.test",
                            password_hash=hashear_password(PASSWORD, rondas=4))
        other = orm.Docente(nombre="Otro docente", correo="otro022@prueba.test",
                            password_hash=hashear_password(PASSWORD, rondas=4))
        s.add_all([owner, other])
        s.flush()
        project = orm.Proyecto(
            docente_id=owner.id, nombre="Proyecto demo TA-022", curso="TI1",
            fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
            url_publica="https://demo.test", elemento_verificar="h1",
        )
        s.add(project)
        s.flush()
        for kind in ("github", "notion", "drive"):
            s.add(orm.Fuente(proyecto_id=project.id, tipo=kind, referencia="dataset:1"))
        s.commit()
        ids = (owner.id, other.id, project.id)

    client = TestClient(app)

    def token(email):
        response = client.post("/auth/login", json={"correo": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    yield client, token("ta022@prueba.test"), token("otro022@prueba.test"), ids[2]

    with Session(engine) as s:
        s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == ids[2]))
        s.delete(s.get(orm.Proyecto, ids[2]))
        s.flush()
        for teacher_id in ids[:2]:
            s.delete(s.get(orm.Docente, teacher_id))
        s.commit()


def consolidate(client, headers, project_id, cutoff):
    return client.post(f"/proyectos/{project_id}/consolidacion", json={"fecha_corte": cutoff},
                       headers=headers)


def test_routes_require_token(api):
    client, _, _, project_id = api
    assert client.post(f"/proyectos/{project_id}/consolidacion").status_code == 401
    for route in ("indicadores", "alertas", "historial"):
        assert client.get(f"/proyectos/{project_id}/{route}").status_code == 401


def test_other_teacher_cannot_see_the_project(api):
    client, _, other, project_id = api
    assert consolidate(client, other, project_id, CUTS[1]).status_code == 404
    assert client.get(f"/proyectos/{project_id}/historial", headers=other).status_code == 404


def test_consolidation_runs_the_graph_and_saves_the_cut(api):
    client, headers, _, project_id = api
    response = consolidate(client, headers, project_id, CUTS[1])
    assert response.status_code == 200, response.text
    body = response.json()

    assert {s: v["estado"] for s, v in body["fuentes"].items()} == {
        "github": "ok", "notion": "ok", "drive": "ok"}
    assert body["total_evidencias"] == 50
    assert body["guardado"]["alertas"] == len(cargar_dataset()["alertas_esperadas"]["1"])
    assert body["guardado"]["alertas_sin_evidencia"] == 0


def test_indicators_alerts_and_history(api):
    client, headers, _, project_id = api
    for cutoff in CUTS:
        assert consolidate(client, headers, project_id, cutoff).status_code == 200

    latest = client.get(f"/proyectos/{project_id}/indicadores", headers=headers).json()
    assert latest["fecha_corte"] == "2026-10-12"
    expected = cargar_dataset()["indicadores_esperados"]["1"]
    assert latest["indicadores"]["I1"] == expected["I1"]
    assert latest["indicadores"]["I3"] == expected["I3"]

    first = client.get(f"/proyectos/{project_id}/indicadores",
                       params={"fecha_corte": "2026-10-06"}, headers=headers)
    assert first.status_code == 200 and first.json()["fecha_corte"] == "2026-10-06"

    alerts = client.get(f"/proyectos/{project_id}/alertas", headers=headers).json()
    assert alerts["total"] == len(cargar_dataset()["alertas_esperadas"]["1"])
    assert all(a["explicacion"] for a in alerts["alertas"])

    history = client.get(f"/proyectos/{project_id}/historial", headers=headers).json()
    assert history["total_cortes"] == 2
    assert [c["fecha_corte"] for c in history["cortes"]] == ["2026-10-06", "2026-10-12"]


def test_errors_are_clear(api):
    client, headers, _, project_id = api
    missing = client.get(f"/proyectos/{project_id}/indicadores",
                         params={"fecha_corte": "2026-01-01"}, headers=headers)
    assert missing.status_code == 404
    bad = client.get(f"/proyectos/{project_id}/alertas",
                     params={"fecha_corte": "12/10/2026"}, headers=headers)
    assert bad.status_code == 422
    assert consolidate(client, headers, project_id, "2026-10-12").status_code == 422  # sin hora ni zona


def test_each_route_answers_in_less_than_two_seconds(api):
    client, headers, _, project_id = api
    assert consolidate(client, headers, project_id, CUTS[1]).status_code == 200
    calls = {
        "consolidacion": lambda: consolidate(client, headers, project_id, CUTS[1]),
        "indicadores": lambda: client.get(f"/proyectos/{project_id}/indicadores", headers=headers),
        "alertas": lambda: client.get(f"/proyectos/{project_id}/alertas", headers=headers),
        "historial": lambda: client.get(f"/proyectos/{project_id}/historial", headers=headers),
    }
    for name, call in calls.items():
        for _ in range(REQUESTS):
            started = time.perf_counter()
            assert call().status_code == 200
            elapsed = time.perf_counter() - started
            assert elapsed < MAX_SECONDS, f"{name} tardó {elapsed:.2f} s"
