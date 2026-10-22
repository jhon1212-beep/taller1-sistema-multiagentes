"""AR-05: contrato del módulo validacion (dominio, puerto y ejecutor falso)."""

from datetime import datetime, timezone

import pytest

from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso
from app.modulos.validacion.dominio import (
    ResultadoValidacion,
    SolicitudValidacion,
    ValidacionInvalida,
)
from app.modulos.validacion.puertos import EjecutorE2E

AHORA = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def solicitud(url="https://demo.example.com"):
    return SolicitudValidacion(proyecto_id=1, url_publica=url, elemento_verificar="#boton")


def test_el_ejecutor_falso_cumple_el_puerto():
    ejecutor: EjecutorE2E = EjecutorE2EFalso(ahora=lambda: AHORA)
    assert ejecutor.ejecutar(solicitud()).resultado == "PASS"


def test_pass_no_lleva_captura_y_trae_run_id():
    r = EjecutorE2EFalso(ahora=lambda: AHORA).ejecutar(solicitud())
    assert r.captura_url is None and r.run_id_actions and r.duracion_ms >= 0


def test_fail_funcional_se_devuelve_con_captura_sin_lanzar_excepcion():
    r = EjecutorE2EFalso(ahora=lambda: AHORA).ejecutar(solicitud("https://falla.example.com"))
    assert r.resultado == "FAIL" and r.captura_url


def test_to_dict_serializa_la_fecha():
    d = EjecutorE2EFalso(ahora=lambda: AHORA).ejecutar(solicitud()).to_dict()
    assert d["ejecutada_en"] == "2026-10-19T12:00:00+00:00"


@pytest.mark.parametrize(
    "cambios",
    [
        {"resultado": "OK"},
        {"duracion_ms": -1},
        {"resultado": "PASS", "captura_url": "x"},
        {"ejecutada_en": datetime(2026, 10, 19, 12, 0)},  # sin zona horaria
    ],
)
def test_resultado_invalido_se_rechaza(cambios):
    datos = dict(proyecto_id=1, resultado="PASS", duracion_ms=10, ejecutada_en=AHORA, run_id_actions=7)
    datos.update(cambios)
    with pytest.raises(ValidacionInvalida):
        ResultadoValidacion(**datos)


def test_solicitud_vacia_se_rechaza():
    with pytest.raises(ValidacionInvalida):
        SolicitudValidacion(proyecto_id=1, url_publica=" ", elemento_verificar="#x")
