# -*- coding: utf-8 -*-
"""HU-002: pruebas del módulo proyectos (servicio y rutas).

Usan el repositorio en memoria: no necesitan PostgreSQL.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.proyectos.adaptadores.memoria import RepositorioProyectosMemoria
from app.modulos.proyectos.rutas import obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos

PROYECTO_VALIDO = {
    "nombre": "Sistema de reservas",
    "curso": "Taller Integrador 1",
    "fecha_inicio": "2026-09-28",
    "fecha_fin": "2026-11-20",
    "url_publica": "https://reservas.example.com",
    "elemento_verificar": "#boton-reservar",
    "integrantes": [{"nombre": "Ana", "correo": "ana@example.com"}, {"nombre": "Luis"}],
    "fuentes": {
        "github": "jhon1212-beep/taller1-sistema-multiagentes",
        "notion": "base-notion-123",
        "drive": "carpeta-drive-456",
    },
}


@pytest.fixture
def cliente():
    servicio = ServicioProyectos(RepositorioProyectosMemoria())
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_cp04_registrar_proyecto_con_todos_los_campos(cliente):
    r = cliente.post("/proyectos", json=PROYECTO_VALIDO)

    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["id"] == 1
    assert cuerpo["activo"] is True
    assert cuerpo["nombre"] == "Sistema de reservas"
    assert len(cuerpo["integrantes"]) == 2
    assert set(cuerpo["fuentes"]) == {"github", "notion", "drive"}

    listado = cliente.get("/proyectos").json()
    assert [p["id"] for p in listado] == [1]


def test_cp05_sin_nombre_no_se_guarda(cliente):
    r = cliente.post("/proyectos", json={**PROYECTO_VALIDO, "nombre": ""})
    assert r.status_code == 422

    r = cliente.post("/proyectos", json={**PROYECTO_VALIDO, "nombre": "   "})
    assert r.status_code == 422
    assert "nombre" in r.json()["detail"].lower()

    assert cliente.get("/proyectos").json() == []


def test_sin_integrantes_no_se_guarda(cliente):
    r = cliente.post("/proyectos", json={**PROYECTO_VALIDO, "integrantes": []})
    assert r.status_code == 422


def test_falta_una_fuente_no_se_guarda(cliente):
    fuentes = {**PROYECTO_VALIDO["fuentes"]}
    del fuentes["drive"]
    r = cliente.post("/proyectos", json={**PROYECTO_VALIDO, "fuentes": fuentes})
    assert r.status_code == 422


def test_fechas_invertidas_no_se_guardan(cliente):
    r = cliente.post(
        "/proyectos",
        json={**PROYECTO_VALIDO, "fecha_inicio": "2026-12-01", "fecha_fin": "2026-11-01"},
    )
    assert r.status_code == 422


def test_url_publica_debe_ser_http(cliente):
    r = cliente.post("/proyectos", json={**PROYECTO_VALIDO, "url_publica": "reservas.example.com"})
    assert r.status_code == 422


def test_ver_un_proyecto_y_404_si_no_existe(cliente):
    cliente.post("/proyectos", json=PROYECTO_VALIDO)

    assert cliente.get("/proyectos/1").status_code == 200
    assert cliente.get("/proyectos/99").status_code == 404


def test_editar_proyecto(cliente):
    cliente.post("/proyectos", json=PROYECTO_VALIDO)

    r = cliente.put("/proyectos/1", json={**PROYECTO_VALIDO, "nombre": "Reservas v2"})

    assert r.status_code == 200
    assert r.json()["nombre"] == "Reservas v2"
    assert cliente.get("/proyectos/1").json()["nombre"] == "Reservas v2"


def test_editar_con_nombre_vacio_conserva_el_original(cliente):
    cliente.post("/proyectos", json=PROYECTO_VALIDO)

    r = cliente.put("/proyectos/1", json={**PROYECTO_VALIDO, "nombre": "  "})

    assert r.status_code == 422
    assert cliente.get("/proyectos/1").json()["nombre"] == "Sistema de reservas"


def test_desactivar_oculta_del_listado_pero_no_borra(cliente):
    cliente.post("/proyectos", json=PROYECTO_VALIDO)

    r = cliente.patch("/proyectos/1/desactivar")

    assert r.status_code == 200
    assert r.json()["activo"] is False
    assert cliente.get("/proyectos").json() == []
    assert len(cliente.get("/proyectos?incluir_inactivos=true").json()) == 1
