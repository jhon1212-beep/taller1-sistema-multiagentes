"""HU-008: rutas de consulta de la validación funcional (CP-17), con login real.

Sin PostgreSQL ni GitHub: repositorios en memoria y el ejecutor falso. Cubre las dos
rutas, el aislamiento por docente y la protección con token.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.autenticacion.adaptadores.memoria import RepositorioDocentesMemoria
from app.modulos.autenticacion.dominio import Docente
from app.modulos.autenticacion.rutas import obtener_servicio_autenticacion
from app.modulos.autenticacion.servicio import ServicioAutenticacionReal, hashear_password
from app.modulos.proyectos.adaptadores.memoria import RepositorioProyectosMemoria
from app.modulos.proyectos.dominio import Integrante, Proyecto
from app.modulos.proyectos.rutas import obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos
from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso
from app.modulos.validacion.adaptadores.memoria import RepositorioValidacionesMemoria
from app.modulos.validacion.dominio import SolicitudValidacion
from app.modulos.validacion.rutas import obtener_repositorio_validaciones
from app.modulos.validacion.servicio import AgenteValidacion

CLAVE = "ClaveDePrueba-2026"  # contraseña de prueba, no es una credencial real
T0 = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)


def un_proyecto(docente_id):
    from datetime import date

    return Proyecto(
        docente_id=docente_id, nombre="Proyecto demo", curso="TI1",
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
        url_publica="https://demo.test", elemento_verificar="h1",
        integrantes=[Integrante("Ana")], fuentes={"github": "o/r", "notion": "n", "drive": "d"},
    )


@pytest.fixture
def entorno():
    docentes = RepositorioDocentesMemoria()
    docentes.agregar(Docente(1, "Docente Uno", "uno@demo.test"), hashear_password(CLAVE, rondas=4))
    docentes.agregar(Docente(2, "Docente Dos", "dos@demo.test"), hashear_password(CLAVE, rondas=4))
    auth = ServicioAutenticacionReal(docentes, "s" * 40)

    proyectos = ServicioProyectos(RepositorioProyectosMemoria())
    propio = proyectos.registrar(un_proyecto(1)).id
    vacio = proyectos.registrar(un_proyecto(1)).id  # propio, pero nunca validado

    # Dos validaciones reales hechas con el Agente de Validación: PASS y luego FAIL.
    validaciones = RepositorioValidacionesMemoria()
    hora = iter(T0 + timedelta(minutes=m) for m in range(10))
    agente = AgenteValidacion(EjecutorE2EFalso(ahora=lambda: next(hora)), validaciones)
    agente.validar(SolicitudValidacion(propio, "https://demo.test", "h1"))
    agente.validar(SolicitudValidacion(propio, "https://falla.test", "h1"))

    app.dependency_overrides[obtener_servicio_autenticacion] = lambda: auth
    app.dependency_overrides[obtener_servicio] = lambda: proyectos
    app.dependency_overrides[obtener_repositorio_validaciones] = lambda: validaciones
    yield TestClient(app), propio, vacio
    app.dependency_overrides.clear()


def entrar(cliente, correo="uno@demo.test"):
    token = cliente.post("/auth/login", json={"correo": correo, "password": CLAVE}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_historial_lista_la_mas_reciente_primero_con_su_recuento(entorno):
    cliente, propio, _ = entorno
    r = cliente.get(f"/proyectos/{propio}/validaciones", headers=entrar(cliente))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["proyecto_id"] == propio
    assert cuerpo["resumen"] == {"PASS": 1, "FAIL": 1}
    assert [i["resultado"] for i in cuerpo["items"]] == ["FAIL", "PASS"]
    assert cuerpo["items"][0]["captura_url"] and cuerpo["items"][1]["captura_url"] is None


def test_historial_se_puede_filtrar_y_acotar(entorno):
    cliente, propio, _ = entorno
    h = entrar(cliente)
    solo_pass = cliente.get(f"/proyectos/{propio}/validaciones?resultado=PASS", headers=h).json()
    assert [i["resultado"] for i in solo_pass["items"]] == ["PASS"]
    assert solo_pass["resumen"] == {"PASS": 1, "FAIL": 1}  # el recuento no depende del filtro
    uno = cliente.get(f"/proyectos/{propio}/validaciones?limite=1", headers=h).json()
    assert len(uno["items"]) == 1


def test_ultima_devuelve_la_validacion_mas_reciente(entorno):
    cliente, propio, _ = entorno
    r = cliente.get(f"/proyectos/{propio}/validaciones/ultima", headers=entrar(cliente))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["resultado"] == "FAIL" and cuerpo["captura_url"]
    assert {"id", "proyecto_id", "duracion_ms", "ejecutada_en", "run_id_actions"} <= set(cuerpo)


def test_proyecto_sin_validaciones_da_historial_vacio_y_ultima_404(entorno):
    cliente, _, vacio = entorno
    h = entrar(cliente)
    historial = cliente.get(f"/proyectos/{vacio}/validaciones", headers=h).json()
    assert historial["items"] == [] and historial["resumen"] == {"PASS": 0, "FAIL": 0}
    r = cliente.get(f"/proyectos/{vacio}/validaciones/ultima", headers=h)
    assert r.status_code == 404 and "validaciones" in r.json()["detail"]


def test_un_docente_no_ve_las_validaciones_de_otro(entorno):
    cliente, propio, _ = entorno
    ajeno = entrar(cliente, "dos@demo.test")
    assert cliente.get(f"/proyectos/{propio}/validaciones", headers=ajeno).status_code == 404
    assert cliente.get(f"/proyectos/{propio}/validaciones/ultima", headers=ajeno).status_code == 404


def test_un_proyecto_que_no_existe_da_404(entorno):
    cliente, _, _ = entorno
    assert cliente.get("/proyectos/999/validaciones", headers=entrar(cliente)).status_code == 404


def test_sin_token_o_con_token_invalido_da_401(entorno):
    cliente, propio, _ = entorno
    for ruta in (f"/proyectos/{propio}/validaciones", f"/proyectos/{propio}/validaciones/ultima"):
        assert cliente.get(ruta).status_code == 401
        assert cliente.get(ruta, headers={"Authorization": "Bearer x"}).status_code == 401


@pytest.mark.parametrize("consulta", ["resultado=MAL", "limite=0", "limite=101", "limite=abc"])
def test_parametros_invalidos_dan_422(entorno, consulta):
    cliente, propio, _ = entorno
    r = cliente.get(f"/proyectos/{propio}/validaciones?{consulta}", headers=entrar(cliente))
    assert r.status_code == 422
