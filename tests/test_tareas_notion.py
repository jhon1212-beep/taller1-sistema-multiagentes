# -*- coding: utf-8 -*-
"""HU-004: pruebas de la vista de tareas (GET /proyectos/{id}/tareas).

Usan el repositorio de proyectos en memoria y, como fuente de Notion, el
dataset controlado de TA-017 o dobles que fallan: no necesitan red ni
PostgreSQL.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.evidencias.adaptadores.notion.cliente import NotionAuthError, NotionError
from app.modulos.evidencias.rutas_tareas import obtener_fuente_tareas
from app.modulos.proyectos.adaptadores.memoria import RepositorioProyectosMemoria
from app.modulos.proyectos.rutas import docente_actual, obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos

PROYECTO = {
    "nombre": "Seguimiento académico",
    "curso": "Taller Integrador 1",
    "fecha_inicio": "2026-09-21",
    "fecha_fin": "2026-11-30",
    "url_publica": "https://example.org",
    "elemento_verificar": "h1",
    "integrantes": [{"nombre": "Ana Torres"}],
    "fuentes": {
        "github": "demo/seguimiento",
        "notion": "base-notion-123",
        "drive": "carpeta-drive-456",
    },
}


class FuenteQueFalla:
    def __init__(self, error):
        self._error = error

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        raise self._error


class FuenteRegistradora(FuenteEvidenciaDataset):
    def __init__(self):
        super().__init__("notion")
        self.llamadas = []

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        self.llamadas.append((referencia, proyecto_id, limite))
        return super().obtener_evidencias(referencia, proyecto_id, limite=limite, desde=desde)


@pytest.fixture
def cliente():
    servicio = ServicioProyectos(RepositorioProyectosMemoria())
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    app.dependency_overrides[obtener_fuente_tareas] = lambda: FuenteEvidenciaDataset("notion")
    c = TestClient(app)
    assert c.post("/proyectos", json=PROYECTO).status_code == 201
    yield c
    app.dependency_overrides.clear()


def test_lista_las_20_tareas_con_sus_campos(cliente):
    r = cliente.get("/proyectos/1/tareas")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "ok" and cuerpo["error"] is None
    assert cuerpo["fuente"] == "notion" and cuerpo["proyecto_id"] == 1
    assert cuerpo["total"] == 20 == len(cuerpo["tareas"])
    primera = cuerpo["tareas"][0]
    assert set(primera) == {"id", "tarea", "responsable", "estado", "fecha_limite", "editada"}
    assert primera["estado"] in ("Sin empezar", "En curso", "Listo")


def test_resumen_por_estado_y_tarea_sin_responsable(cliente):
    resumen = cliente.get("/proyectos/1/tareas").json()["resumen"]
    assert resumen == {"listo": 8, "en_curso": 6, "sin_empezar": 6, "sin_responsable": 1}


def test_la_tarea_sin_responsable_llega_como_null(cliente):
    tareas = cliente.get("/proyectos/1/tareas").json()["tareas"]
    assert [t["responsable"] for t in tareas].count(None) == 1


def test_limite_reduce_el_resultado(cliente):
    cuerpo = cliente.get("/proyectos/1/tareas?limite=5").json()
    assert cuerpo["total"] == 5


def test_limite_fuera_de_rango_es_422(cliente):
    assert cliente.get("/proyectos/1/tareas?limite=0").status_code == 422
    assert cliente.get("/proyectos/1/tareas?limite=500").status_code == 422


def test_se_consulta_la_base_de_notion_registrada_en_el_proyecto(cliente):
    fuente = FuenteRegistradora()
    app.dependency_overrides[obtener_fuente_tareas] = lambda: fuente
    cliente.get("/proyectos/1/tareas?limite=7")
    assert fuente.llamadas == [("base-notion-123", 1, 7)]


def test_credenciales_rechazadas_no_inventan_tareas(cliente):
    app.dependency_overrides[obtener_fuente_tareas] = lambda: FuenteQueFalla(
        NotionAuthError("HTTP 401: token inválido")
    )
    r = cliente.get("/proyectos/1/tareas")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "fallo"
    assert cuerpo["total"] == 0 and cuerpo["tareas"] == []
    assert "Notion" in cuerpo["error"] and "credenciales" in cuerpo["error"]
    assert "token inválido" not in cuerpo["error"]  # el detalle técnico no se expone


def test_error_de_red_queda_como_fallo_controlado(cliente):
    app.dependency_overrides[obtener_fuente_tareas] = lambda: FuenteQueFalla(
        NotionError("Error de red al consultar Notion: timeout")
    )
    cuerpo = cliente.get("/proyectos/1/tareas").json()
    assert cuerpo["estado"] == "fallo" and cuerpo["tareas"] == []
    assert "Notion" in cuerpo["error"]


def test_proyecto_inexistente_es_404(cliente):
    assert cliente.get("/proyectos/99/tareas").status_code == 404


def test_un_docente_no_ve_las_tareas_de_otro(cliente):
    app.dependency_overrides[docente_actual] = lambda: 2
    assert cliente.get("/proyectos/1/tareas").status_code == 404
