"""TA-018: historial por fecha de corte en PostgreSQL.

Criterios: 1) persiste un corte por proyecto y fecha; 2) el historial
devuelve al menos 2 cortes del proyecto demo. Necesita DATABASE_URL con la
migración aplicada (alembic upgrade head); sin base, la prueba se omite.
"""
import os
from datetime import date, datetime, timezone

import pytest

pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine, func, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido import modelos_orm as orm  # noqa: E402
from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402
from app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository, cutoff_day  # noqa: E402
from app.modulos.supervision.service import SupervisionService  # noqa: E402
from app.modulos.supervision.sources import build_explainer, build_source_adapters  # noqa: E402

URL = os.getenv("DATABASE_URL", "")
FIRST_CUT = "2026-10-06T23:59:59-05:00"
SECOND_CUT = "2026-10-12T23:59:59-05:00"  # = fecha_corte del dataset TA-017
REFERENCES = {"github": "dataset:1", "notion": "dataset:1", "drive": "dataset:1"}


@pytest.fixture
def session():
    if not URL:
        pytest.skip("Falta DATABASE_URL.")
    engine = create_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1 from indicador limit 1"))
    except Exception as error:  # base caída o sin migrar
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")
    with Session(engine) as s:
        teacher = orm.Docente(nombre="Docente TA-018", correo="ta018@prueba.test", password_hash="x")
        s.add(teacher)
        s.flush()
        project = orm.Proyecto(
            docente_id=teacher.id, nombre="Proyecto demo TA-018", curso="TI1",
            fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
            url_publica="https://demo.test", elemento_verificar="h1",
        )
        s.add(project)
        s.flush()
        for kind, ref in REFERENCES.items():
            s.add(orm.Fuente(proyecto_id=project.id, tipo=kind, referencia=ref))
        s.commit()
        yield s, project.id
        s.rollback()
        # alerta.evidencia_id no tiene ON DELETE CASCADE: se borran primero las alertas.
        s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == project.id))
        s.delete(s.get(orm.Proyecto, project.id))
        s.flush()
        s.delete(teacher)
        s.commit()


def run(s, project_id, cutoff):
    service = SupervisionService(SqlSupervisionRepository(s), build_source_adapters("dataset"),
                                 build_explainer("template"))
    return service.run_cutoff(project_id, REFERENCES, cutoff)


def test_cutoff_day_uses_local_calendar_day():
    # 23:59 en Lima ya es el día siguiente en UTC; el corte es del 12.
    assert cutoff_day(SECOND_CUT) == date(2026, 10, 12)
    assert cutoff_day("2026-10-13T04:59:59Z") == date(2026, 10, 13)
    assert cutoff_day("2026-10-12") == date(2026, 10, 12)


def test_one_cutoff_per_project_and_day_is_persisted(session):
    s, project_id = session
    first = run(s, project_id, SECOND_CUT)
    again = run(s, project_id, SECOND_CUT)  # mismo día: reemplaza, no duplica

    assert first["guardado"] == again["guardado"]
    indicator_rows = s.scalar(select(func.count()).select_from(orm.Indicador)
                              .where(orm.Indicador.proyecto_id == project_id))
    alert_rows = s.scalar(select(func.count()).select_from(orm.Alerta)
                          .where(orm.Alerta.proyecto_id == project_id))
    evidence_rows = s.scalar(select(func.count()).select_from(orm.Evidencia)
                             .where(orm.Evidencia.proyecto_id == project_id))
    assert indicator_rows == 1
    assert alert_rows == len(cargar_dataset()["alertas_esperadas"]["1"])
    assert evidence_rows == 50  # 20 commits + 20 tareas + 10 documentos del proyecto demo 1


def test_saved_values_match_the_ta017_spreadsheet(session):
    s, project_id = session
    run(s, project_id, SECOND_CUT)
    state = SqlSupervisionRepository(s).obtener(project_id, SECOND_CUT)

    expected_ind = cargar_dataset()["indicadores_esperados"]["1"]
    saved_ind = state["indicadores"]
    assert {k: saved_ind[k] for k in ("I1", "I3", "I4")} == {k: expected_ind[k] for k in ("I1", "I3", "I4")}
    # I2 según el Charter v6.0: Sin empezar + En curso = total - Listo. El JSON de
    # TA-017 trae 30.0 porque se generó con motor.py (solo "Sin empezar"); ver la guía.
    assert saved_ind["I2"] == round(100 - saved_ind["I1"], 2)
    expected = {(a["regla"], a["evidencia_id"]) for a in cargar_dataset()["alertas_esperadas"]["1"]}
    assert {(a["regla"], a["evidencia_ids"][0]) for a in state["alertas"]} == expected
    # RN-003: cada alerta guardada tiene evidencia y explicación.
    assert all(a["explicacion"] and a["origen_explicacion"] == "plantilla" for a in state["alertas"])


def test_history_returns_two_cutoffs_in_order(session):
    s, project_id = session
    run(s, project_id, SECOND_CUT)
    run(s, project_id, FIRST_CUT)  # orden de ejecución distinto al cronológico
    s.add(orm.Validacion(  # TA-021 registró una validación el día del segundo corte
        proyecto_id=project_id, resultado="PASS", duracion_ms=1800,
        ejecutada_en=datetime(2026, 10, 12, 20, 0, tzinfo=timezone.utc), run_id_actions=1,
    ))
    s.commit()

    history = SqlSupervisionRepository(s).history(project_id)

    assert [c["fecha_corte"] for c in history] == ["2026-10-06", "2026-10-12"]
    assert history[1]["validacion"]["resultado"] == "PASS"
    assert history[0]["validacion"] is None
    # El historial muestra la evolución: el I4 o las alertas cambian entre cortes.
    assert history[0] != history[1]


def test_unknown_cutoff_returns_none(session):
    s, project_id = session
    assert SqlSupervisionRepository(s).obtener(project_id, "2026-01-01") is None
