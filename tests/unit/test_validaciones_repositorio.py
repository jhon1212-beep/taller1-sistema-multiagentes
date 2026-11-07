"""TA-048: repositorio de validaciones (registrar, última, historial y recuento).

El mismo contrato se comprueba con el repositorio en memoria y con el de SQL sobre
SQLite en memoria; así se prueba la consulta real sin necesitar PostgreSQL.
El caso contra PostgreSQL está en tests/test_validacion_postgres.py.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.modulos.validacion.adaptadores.memoria import RepositorioValidacionesMemoria
from app.modulos.validacion.adaptadores.sql import RepositorioValidacionesSQL
from app.modulos.validacion.dominio import ResultadoValidacion, ValidacionInvalida

T0 = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)


def resultado(proyecto_id=1, veredicto="PASS", minutos=0, run_id=555):
    return ResultadoValidacion(
        proyecto_id=proyecto_id,
        resultado=veredicto,
        duracion_ms=1500,
        ejecutada_en=T0 + timedelta(minutes=minutos),
        run_id_actions=run_id,
        captura_url="https://ejemplo.invalid/captura.png" if veredicto == "FAIL" else None,
    )


@pytest.fixture(params=["memoria", "sql"])
def repo(request):
    if request.param == "memoria":
        yield RepositorioValidacionesMemoria()
        return
    motor = create_engine("sqlite://")
    orm.Validacion.__table__.create(motor)  # SQLite no exige que exista `proyecto`
    with Session(motor) as sesion:
        yield RepositorioValidacionesSQL(sesion)


def test_registrar_devuelve_ids_distintos_y_crecientes(repo):
    ids = [repo.registrar(resultado(minutos=m)) for m in range(3)]
    assert ids == sorted(set(ids)) and len(ids) == 3


def test_un_proyecto_sin_validaciones_no_es_un_error(repo):
    assert repo.ultima(1) is None
    assert repo.listar(1) == []
    assert repo.contar(1) == {"PASS": 0, "FAIL": 0}


def test_ultima_es_la_mas_reciente_por_fecha_no_por_orden_de_insercion(repo):
    repo.registrar(resultado(veredicto="FAIL", minutos=30))  # la más reciente, insertada primero
    repo.registrar(resultado(veredicto="PASS", minutos=5))
    ultima = repo.ultima(1)
    assert ultima.resultado.resultado == "FAIL"
    assert ultima.resultado.ejecutada_en == T0 + timedelta(minutes=30)


def test_listar_va_de_la_mas_reciente_a_la_mas_antigua(repo):
    for m, v in ((10, "PASS"), (40, "FAIL"), (20, "PASS")):
        repo.registrar(resultado(veredicto=v, minutos=m))
    fechas = [g.resultado.ejecutada_en for g in repo.listar(1)]
    assert fechas == sorted(fechas, reverse=True) and len(fechas) == 3


def test_listar_respeta_el_limite(repo):
    for m in range(5):
        repo.registrar(resultado(minutos=m))
    assert len(repo.listar(1, limite=2)) == 2
    assert repo.listar(1, limite=2)[0].resultado.ejecutada_en == T0 + timedelta(minutes=4)


def test_listar_filtra_por_resultado(repo):
    repo.registrar(resultado(veredicto="PASS", minutos=1))
    repo.registrar(resultado(veredicto="FAIL", minutos=2))
    repo.registrar(resultado(veredicto="PASS", minutos=3))
    assert [g.resultado.resultado for g in repo.listar(1, resultado="FAIL")] == ["FAIL"]
    assert len(repo.listar(1, resultado="PASS")) == 2


def test_contar_cuenta_todas_las_validaciones_del_proyecto(repo):
    for v in ("PASS", "FAIL", "PASS", "PASS"):
        repo.registrar(resultado(veredicto=v))
    assert repo.contar(1) == {"PASS": 3, "FAIL": 1}


def test_cada_proyecto_ve_solo_sus_validaciones(repo):
    repo.registrar(resultado(proyecto_id=1, veredicto="PASS"))
    repo.registrar(resultado(proyecto_id=2, veredicto="FAIL"))
    assert repo.ultima(1).resultado.resultado == "PASS"
    assert repo.ultima(2).resultado.resultado == "FAIL"
    assert repo.contar(1) == {"PASS": 1, "FAIL": 0}
    assert [g.resultado.proyecto_id for g in repo.listar(2)] == [2]


def test_un_fail_conserva_su_captura_y_un_pass_no_la_tiene(repo):
    repo.registrar(resultado(veredicto="PASS", minutos=1))
    repo.registrar(resultado(veredicto="FAIL", minutos=2))
    fail, pass_ = repo.listar(1)
    assert fail.resultado.captura_url and pass_.resultado.captura_url is None


def test_se_conservan_el_run_la_duracion_y_la_zona_horaria(repo):
    repo.registrar(resultado(run_id=987654321))
    g = repo.ultima(1)
    assert (g.resultado.run_id_actions, g.resultado.duracion_ms) == (987654321, 1500)
    assert g.resultado.ejecutada_en.tzinfo is not None
    assert g.to_dict()["id"] == g.id


@pytest.mark.parametrize(
    "argumentos",
    [{"resultado": "MAL"}, {"limite": 0}, {"limite": 101}],
    ids=["resultado_invalido", "limite_cero", "limite_excesivo"],
)
def test_parametros_invalidos_lanzan_validacion_invalida(repo, argumentos):
    with pytest.raises(ValidacionInvalida):
        repo.listar(1, **argumentos)
