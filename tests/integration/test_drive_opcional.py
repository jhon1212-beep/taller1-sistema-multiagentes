"""Drive opcional: un proyecto puede supervisarse solo con GitHub y Notion.

Cubre el grafo (estado "no_configurada", sin R4) y, si hay PostgreSQL, el
repositorio de cortes y la ruta de documentos.
"""
from __future__ import annotations

import os
from datetime import date

import pytest

pytest.importorskip("langgraph")

from app.modulos.supervision.grafo.supervisor import (  # noqa: E402
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.sources import build_explainer, build_source_adapters  # noqa: E402

CUTOFF = "2026-10-12T23:59:59-05:00"  # fecha de corte del dataset TA-017
CON_DRIVE = {"github": "dataset:1", "notion": "dataset:1", "drive": "dataset:1"}
SIN_DRIVE = {"github": "dataset:1", "notion": "dataset:1"}


def _run(references):
    graph = build_supervisor_graph(build_source_adapters("dataset"), explainer=build_explainer("template"))
    return graph.invoke(build_supervisor_input(1, CUTOFF, references))


def test_sin_drive_la_fuente_queda_no_configurada_y_sin_error():
    final = _run(SIN_DRIVE)

    assert final["estado_fuentes"] == {"github": "ok", "notion": "ok", "drive": "no_configurada"}
    assert final["errores_fuentes"]["drive"] is None
    assert all(e.fuente != "drive" for e in final["evidencias"])


def test_sin_drive_no_hay_alerta_r4_ni_alertas_de_drive():
    final = _run(SIN_DRIVE)

    assert all(a["regla"] != "R4" and a["fuente"] != "drive" for a in final["alertas"])
    # Toda alerta sigue teniendo explicación y evidencia (RN-003).
    assert all(a["explicacion"] and a["evidencia_ids"] for a in final["alertas"])


def test_sin_drive_los_indicadores_de_tareas_no_cambian():
    """I1-I3 salen de Notion: quitar Drive no los altera."""
    con, sin = _run(CON_DRIVE), _run(SIN_DRIVE)

    for clave in ("I1", "I2", "I3"):
        assert sin["indicadores"][clave] == con["indicadores"][clave]
    # Las alertas de GitHub y Notion son las mismas con o sin Drive.
    reglas = lambda f: sorted((a["regla"], tuple(a["evidencia_ids"])) for a in f["alertas"] if a["fuente"] != "drive")
    assert reglas(sin) == reglas(con)


def test_consolidado_informa_drive_no_configurada():
    report = to_consolidated_report(_run(SIN_DRIVE))

    assert report["fuentes"]["drive"] == {
        "estado": "no_configurada", "error": None, "evidencias": 0, "fuera_de_corte": 0,
    }


# -- con PostgreSQL ------------------------------------------------------------

URL = os.getenv("DATABASE_URL", "")


@pytest.fixture
def proyecto_sin_drive():
    if not URL:
        pytest.skip("Falta DATABASE_URL.")
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from app.compartido import modelos_orm as orm

    engine = create_engine(URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1 from indicador limit 1"))
    except Exception as error:  # base caída o sin migrar
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")
    with Session(engine) as s:
        teacher = orm.Docente(nombre="Docente Drive opcional", correo="drive-opcional@prueba.test",
                              password_hash="x")
        s.add(teacher)
        s.flush()
        project = orm.Proyecto(
            docente_id=teacher.id, nombre="Proyecto sin Drive", curso="TI1",
            fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
            url_publica="https://demo.test", elemento_verificar="h1",
        )
        s.add(project)
        s.flush()
        for kind, ref in SIN_DRIVE.items():
            s.add(orm.Fuente(proyecto_id=project.id, tipo=kind, referencia=ref))
        s.commit()
        yield s, project.id
        s.rollback()
        s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == project.id))
        s.delete(s.get(orm.Proyecto, project.id))
        s.flush()
        s.delete(teacher)
        s.commit()


def test_corte_sin_drive_se_guarda_y_se_consulta(proyecto_sin_drive):
    from app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository
    from app.modulos.supervision.service import SupervisionService

    s, project_id = proyecto_sin_drive
    service = SupervisionService(SqlSupervisionRepository(s), build_source_adapters("dataset"),
                                 build_explainer("template"))

    report = service.run_cutoff(project_id, SIN_DRIVE, CUTOFF)
    assert report["fuentes"]["drive"]["estado"] == "no_configurada"
    assert report["guardado"]["alertas_sin_evidencia"] == 0

    consulta = service.indicators(project_id, "2026-10-12")
    assert consulta["estado_fuentes"]["drive"] == "no_configurada"
    assert consulta["estado_fuentes"]["github"] == "ok"
    assert all(a["regla"] != "R4" for a in service.alerts(project_id, "2026-10-12")["alertas"])
