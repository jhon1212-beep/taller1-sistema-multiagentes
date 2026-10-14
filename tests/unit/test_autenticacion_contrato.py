"""AR-04 · Pruebas del contrato del módulo autenticacion."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modulos.autenticacion.adaptadores.falso import CLAVE_DEMO, ServicioAutenticacionFalso
from app.modulos.autenticacion.dominio import CredencialesInvalidas, SesionInvalida


class Reloj:
    def __init__(self):
        self.t = datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


def test_login_correcto_devuelve_sesion_y_docente():
    svc = ServicioAutenticacionFalso()
    sesion = svc.iniciar_sesion("docente1@demo.test", CLAVE_DEMO)
    docente = svc.obtener_docente(sesion.token)
    assert docente.id == sesion.docente_id == 1
    assert docente.correo == "docente1@demo.test"
    assert not hasattr(docente, "password_hash")


def test_correo_se_normaliza():
    svc = ServicioAutenticacionFalso()
    assert svc.iniciar_sesion("  Docente2@DEMO.test ", CLAVE_DEMO).docente_id == 2


@pytest.mark.parametrize(
    "correo,clave",
    [("docente1@demo.test", "mala"), ("nadie@demo.test", CLAVE_DEMO), ("", "")],
)
def test_credenciales_incorrectas(correo, clave):
    with pytest.raises(CredencialesInvalidas):
        ServicioAutenticacionFalso().iniciar_sesion(correo, clave)


def test_docente_inactivo_no_inicia_sesion():
    from app.modulos.autenticacion.dominio import Docente

    svc = ServicioAutenticacionFalso([(Docente(9, "Baja", "baja@demo.test", activo=False), "x")])
    with pytest.raises(CredencialesInvalidas):
        svc.iniciar_sesion("baja@demo.test", "x")


def test_token_desconocido():
    with pytest.raises(SesionInvalida):
        ServicioAutenticacionFalso().obtener_docente("inventado")


def test_cerrar_sesion_invalida_el_token_y_es_idempotente():
    svc = ServicioAutenticacionFalso()
    token = svc.iniciar_sesion("docente1@demo.test", CLAVE_DEMO).token
    svc.cerrar_sesion(token)
    svc.cerrar_sesion(token)
    with pytest.raises(SesionInvalida):
        svc.obtener_docente(token)


def test_la_sesion_expira():
    reloj = Reloj()
    svc = ServicioAutenticacionFalso(ahora=reloj, duracion=timedelta(hours=1))
    token = svc.iniciar_sesion("docente1@demo.test", CLAVE_DEMO).token
    reloj.t += timedelta(minutes=59)
    assert svc.obtener_docente(token).id == 1
    reloj.t += timedelta(minutes=2)
    with pytest.raises(SesionInvalida):
        svc.obtener_docente(token)


def test_dos_sesiones_tienen_tokens_distintos():
    svc = ServicioAutenticacionFalso()
    a = svc.iniciar_sesion("docente1@demo.test", CLAVE_DEMO)
    b = svc.iniciar_sesion("docente1@demo.test", CLAVE_DEMO)
    assert a.token != b.token
