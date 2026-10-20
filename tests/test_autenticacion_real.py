"""HU-001: login real (bcrypt + JWT) y rutas protegidas. Sin PostgreSQL."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.autenticacion.adaptadores.memoria import RepositorioDocentesMemoria
from app.modulos.autenticacion.dominio import (
    CredencialesInvalidas,
    Docente,
    SesionInvalida,
)
from app.modulos.autenticacion.rutas import docente_actual, obtener_servicio_autenticacion
from app.modulos.autenticacion.servicio import ServicioAutenticacionReal, hashear_password
from app.modulos.proyectos.adaptadores.memoria import RepositorioProyectosMemoria
from app.modulos.proyectos.rutas import docente_actual as docente_temporal
from app.modulos.proyectos.rutas import obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos

SECRETO = "s" * 40  # secreto de prueba, no es una credencial real
CLAVE = "ClaveDePrueba-2026"
T0 = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


class Reloj:
    def __init__(self):
        self.ahora = T0

    def __call__(self):
        return self.ahora


def repo():
    r = RepositorioDocentesMemoria()
    r.agregar(Docente(1, "Docente Uno", "uno@demo.test"), hashear_password(CLAVE, rondas=4))
    r.agregar(Docente(2, "Docente Dos", "dos@demo.test"), hashear_password(CLAVE, rondas=4))
    r.agregar(Docente(3, "Inactivo", "off@demo.test", activo=False), hashear_password(CLAVE, rondas=4))
    return r


def servicio(reloj=None, cerradas=None):
    return ServicioAutenticacionReal(
        repo(), SECRETO, ahora=reloj or Reloj(), sesiones_cerradas=cerradas
    )


# -- servicio ---------------------------------------------------------------
def test_login_correcto_devuelve_jwt_del_docente():
    sesion = servicio().iniciar_sesion("UNO@demo.test", CLAVE)
    datos = jwt.decode(sesion.token, SECRETO, algorithms=["HS256"], options={"verify_exp": False})
    assert datos["sub"] == "1" and sesion.expira_en == T0 + timedelta(hours=8)


@pytest.mark.parametrize(
    "correo,clave",
    [("uno@demo.test", "otra"), ("nadie@demo.test", CLAVE), ("off@demo.test", CLAVE)],
)
def test_credenciales_invalidas_usan_el_mismo_error(correo, clave):
    with pytest.raises(CredencialesInvalidas) as e:
        servicio().iniciar_sesion(correo, clave)
    assert str(e.value) == "Correo o contraseña incorrectos."


def test_la_clave_se_guarda_con_bcrypt_y_nunca_en_claro():
    h = hashear_password(CLAVE, rondas=4)
    assert h.startswith("$2") and CLAVE not in h


def test_obtener_docente_con_token_vigente():
    s = servicio()
    assert s.obtener_docente(s.iniciar_sesion("uno@demo.test", CLAVE).token).id == 1


def test_token_expirado():
    reloj = Reloj()
    s = servicio(reloj)
    token = s.iniciar_sesion("uno@demo.test", CLAVE).token
    reloj.ahora = T0 + timedelta(hours=8, seconds=1)
    with pytest.raises(SesionInvalida):
        s.obtener_docente(token)


def test_token_manipulado_o_firmado_con_otro_secreto():
    s = servicio()
    falso = jwt.encode({"sub": "1", "exp": 9999999999, "jti": "x"}, "o" * 40, algorithm="HS256")
    for token in (falso, "no-es-un-jwt"):
        with pytest.raises(SesionInvalida):
            s.obtener_docente(token)


def test_cerrar_sesion_invalida_el_token_y_es_idempotente():
    s = servicio()
    token = s.iniciar_sesion("uno@demo.test", CLAVE).token
    s.cerrar_sesion(token)
    s.cerrar_sesion(token)
    s.cerrar_sesion("basura")
    with pytest.raises(SesionInvalida):
        s.obtener_docente(token)


def test_secreto_corto_se_rechaza():
    with pytest.raises(ValueError):
        ServicioAutenticacionReal(repo(), "corto")


# -- rutas ------------------------------------------------------------------
@pytest.fixture
def cliente():
    cerradas: set[str] = set()
    app.dependency_overrides[obtener_servicio_autenticacion] = lambda: servicio(cerradas=cerradas)
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(cliente, correo="uno@demo.test", clave=CLAVE):
    return cliente.post("/auth/login", json={"correo": correo, "password": clave})


def test_ruta_login_ok_y_me(cliente):
    r = login(cliente)
    assert r.status_code == 200 and r.json()["docente"]["correo"] == "uno@demo.test"
    me = cliente.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert me.status_code == 200 and me.json()["id"] == 1


def test_ruta_login_incorrecto_da_401_sin_revelar_si_existe_el_correo(cliente):
    a = login(cliente, clave="mala")
    b = login(cliente, correo="nadie@demo.test")
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_me_sin_token_o_con_token_invalido_da_401(cliente):
    assert cliente.get("/auth/me").status_code == 401
    assert cliente.get("/auth/me", headers={"Authorization": "Bearer x"}).status_code == 401


def test_logout_cierra_la_sesion(cliente):
    token = login(cliente).json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    assert cliente.post("/auth/logout", headers=h).status_code == 204
    assert cliente.get("/auth/me", headers=h).status_code == 401


def test_cp08_rutas_de_proyectos_protegidas_y_aisladas_por_docente(cliente):
    """Cierra el bloqueo de CP-08: al cambiar docente_actual temporal por el real,
    sin token no hay acceso y cada docente solo ve sus proyectos."""
    proyectos = ServicioProyectos(RepositorioProyectosMemoria())
    app.dependency_overrides[obtener_servicio] = lambda: proyectos
    app.dependency_overrides[docente_temporal] = docente_actual
    cuerpo = {
        "nombre": "P", "curso": "C", "fecha_inicio": "2026-09-28", "fecha_fin": "2026-11-20",
        "url_publica": "https://x.example.com", "elemento_verificar": "#a",
        "integrantes": [{"nombre": "Ana"}],
        "fuentes": {"github": "o/r", "notion": "n", "drive": "d"},
    }
    h1 = {"Authorization": f"Bearer {login(cliente).json()['token']}"}
    h2 = {"Authorization": f"Bearer {login(cliente, 'dos@demo.test').json()['token']}"}

    assert cliente.get("/proyectos").status_code == 401
    creado = cliente.post("/proyectos", json=cuerpo, headers=h1)
    assert creado.status_code == 201
    assert len(cliente.get("/proyectos", headers=h1).json()) == 1
    assert cliente.get("/proyectos", headers=h2).json() == []
    assert cliente.get(f"/proyectos/{creado.json()['id']}", headers=h2).status_code == 404
