# -*- coding: utf-8 -*-
"""TA-038: pruebas de las 3 rutas de evidencias (sin base de datos)."""
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.compartido.db import obtener_sesion
from app.modulos.evidencias import rutas, servicio

AHORA = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)

RUTAS = [
    ("commits", "github", {"id_externo": "a" * 40}, "sha"),
    ("tareas", "notion", {"estado": "En curso", "fecha_limite": date(2026, 10, 30)}, "tarea"),
    ("documentos", "drive", {"tipo_archivo": "application/pdf"}, "nombre"),
]


def _fuente(estado="ok"):
    return SimpleNamespace(estado=estado, ultima_sincronizacion=AHORA)


def _evidencia(**extra):
    base = dict(id_externo="x", autor="ana", fecha=AHORA, descripcion="texto",
                estado=None, fecha_limite=None, tipo_archivo=None)
    base.update(extra)
    return SimpleNamespace(**base)


@pytest.fixture
def cliente():
    app = FastAPI()
    app.include_router(rutas.router)
    app.dependency_overrides[obtener_sesion] = lambda: None
    return TestClient(app)


def _simular(monkeypatch, resultado, llamadas=None):
    def falso(sesion, proyecto_id, tipo, limite=None):
        if llamadas is not None:
            llamadas.append((tipo, limite))
        return resultado
    monkeypatch.setattr(servicio, "consultar_fuente", falso)


@pytest.mark.parametrize("ruta,tipo,extra,campo", RUTAS)
def test_ruta_responde_con_estado_ok(cliente, monkeypatch, ruta, tipo, extra, campo):
    llamadas = []
    _simular(monkeypatch, (_fuente("ok"), [_evidencia(**extra)]), llamadas)

    resp = cliente.get(f"/proyectos/1/{ruta}")

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["estado_fuente"] == "ok"
    assert cuerpo["total"] == 1
    assert campo in cuerpo["items"][0]
    assert llamadas[0][0] == tipo


@pytest.mark.parametrize("ruta,tipo,extra,campo", RUTAS)
def test_ruta_informa_fallo_de_la_fuente(cliente, monkeypatch, ruta, tipo, extra, campo):
    _simular(monkeypatch, (_fuente("fallo"), []))

    cuerpo = cliente.get(f"/proyectos/1/{ruta}").json()

    assert cuerpo["estado_fuente"] == "fallo"
    assert cuerpo["items"] == []


def test_fuente_no_registrada_se_reporta_como_fallo(cliente, monkeypatch):
    _simular(monkeypatch, (None, []))

    cuerpo = cliente.get("/proyectos/1/documentos").json()

    assert cuerpo["estado_fuente"] == "fallo"
    assert cuerpo["ultima_extraccion"] is None


def test_proyecto_inexistente_devuelve_404(cliente, monkeypatch):
    _simular(monkeypatch, None)
    assert cliente.get("/proyectos/999/commits").status_code == 404


def test_commits_pide_como_maximo_20(cliente, monkeypatch):
    llamadas = []
    _simular(monkeypatch, (_fuente(), []), llamadas)

    cliente.get("/proyectos/1/commits")

    assert llamadas[0] == ("github", 20)