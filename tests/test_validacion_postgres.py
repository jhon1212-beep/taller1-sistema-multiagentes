"""TA-021: el Agente de Validación registra PASS y FAIL en PostgreSQL.

Necesita DATABASE_URL apuntando a una base con la migración aplicada
(alembic upgrade head). Si no hay base alcanzable, la prueba se omite.
"""

import os
from datetime import date

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido import modelos_orm as orm  # noqa: E402
from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso  # noqa: E402
from app.modulos.validacion.adaptadores.sql import RegistroValidacionSQL  # noqa: E402
from app.modulos.validacion.dominio import SolicitudValidacion  # noqa: E402
from app.modulos.validacion.servicio import AgenteValidacion  # noqa: E402

URL = os.getenv("DATABASE_URL", "")


@pytest.fixture
def sesion():
    if not URL:
        pytest.skip("Falta DATABASE_URL.")
    motor = create_engine(URL)
    try:
        with motor.connect() as c:
            c.execute(text("select 1 from validacion limit 1"))
    except Exception as error:  # base caída o sin migrar
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")
    with Session(motor) as s:
        docente = orm.Docente(nombre="Docente TA-021", correo="ta021@prueba.test", password_hash="x")
        s.add(docente)
        s.flush()
        proyecto = orm.Proyecto(
            docente_id=docente.id, nombre="Proyecto TA-021", curso="TI1",
            fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
            url_publica="https://demo.test", elemento_verificar="h1",
        )
        s.add(proyecto)
        s.commit()
        yield s, proyecto.id
        s.rollback()
        s.delete(s.get(orm.Proyecto, proyecto.id))  # sus validaciones caen en cascada
        s.flush()
        s.delete(docente)
        s.commit()


def test_pass_y_fail_quedan_registrados(sesion):
    s, proyecto_id = sesion
    agente = AgenteValidacion(EjecutorE2EFalso(), RegistroValidacionSQL(s))
    agente.validar(SolicitudValidacion(proyecto_id, "https://demo.test", "h1"))
    agente.validar(SolicitudValidacion(proyecto_id, "https://falla.test", "h1"))

    filas = s.scalars(
        select(orm.Validacion).where(orm.Validacion.proyecto_id == proyecto_id).order_by(orm.Validacion.id)
    ).all()
    assert [f.resultado for f in filas] == ["PASS", "FAIL"]
    assert filas[0].captura_url is None and filas[1].captura_url
    assert all(f.run_id_actions is not None and f.ejecutada_en.tzinfo for f in filas)
