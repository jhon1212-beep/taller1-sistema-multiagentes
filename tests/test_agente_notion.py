# -*- coding: utf-8 -*-
"""TA-007: pruebas del adaptador y del agente Notion.

Simulan el cliente para evitar llamadas a la API real.
"""
import logging

from app.modulos.evidencias.adaptadores.notion import adaptador
from app.modulos.evidencias.adaptadores.notion.cliente import (
    NotionAuthError,
    NotionClient,
    _normalizar_pagina,
)
from app.modulos.evidencias.agentes.agente_notion import agente_notion

PROYECTO_ID = 1
BASE_ID = "base-demo-123"

PAGINA_CRUDA = {
    "id": "pagina-001",
    "last_edited_time": "2026-10-01T10:00:00.000Z",
    "properties": {
        "Tarea": {"title": [{"plain_text": "Diseñar "}, {"plain_text": "prototipo"}]},
        "Responsable": {"people": [{"name": "Ana"}, {"name": "Luis"}]},
        "Estado": {"status": {"name": "En curso"}},
        "Fecha límite": {"date": {"start": "2026-10-10"}},
    },
}

PAGINA_SIN_RESPONSABLE = {
    "id": "pagina-002",
    "last_edited_time": "2026-10-02T09:00:00.000Z",
    "properties": {
        "Tarea": {"title": [{"plain_text": "Tarea huérfana"}]},
        "Responsable": {"people": []},
        "Estado": {"status": None},
        "Fecha límite": {"date": None},
    },
}


def test_normalizar_pagina_extrae_las_4_propiedades():
    tarea = _normalizar_pagina(PAGINA_CRUDA)

    assert tarea["tarea"] == "Diseñar prototipo"
    assert tarea["responsable"] == "Ana, Luis"
    assert tarea["estado"] == "En curso"
    assert tarea["fecha_limite"] == "2026-10-10"


def test_normalizar_pagina_tolera_propiedades_vacias():
    tarea = _normalizar_pagina(PAGINA_SIN_RESPONSABLE)

    assert tarea["responsable"] is None
    assert tarea["estado"] is None
    assert tarea["fecha_limite"] is None


def test_normalizar_tarea_mapea_al_esquema_comun():
    evidencia = adaptador._normalizar_tarea(_normalizar_pagina(PAGINA_CRUDA), PROYECTO_ID)

    assert evidencia.fuente == "notion"
    assert evidencia.id_externo == "pagina-001"
    assert evidencia.autor == "Ana, Luis"
    assert evidencia.fecha == "2026-10-01T10:00:00.000Z"
    assert evidencia.descripcion == "Diseñar prototipo"
    assert evidencia.proyecto_id == PROYECTO_ID
    assert evidencia.estado == "En curso"
    assert evidencia.fecha_limite == "2026-10-10"


def test_tarea_sin_responsable_deja_autor_en_none():
    evidencia = adaptador._normalizar_tarea(
        _normalizar_pagina(PAGINA_SIN_RESPONSABLE), PROYECTO_ID
    )

    assert evidencia.autor is None


def test_agente_notion_pide_como_maximo_20_tareas(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "token-falso")
    llamadas = {}

    def tareas_falsas(self, database_id, desde=None, maximo=None):
        llamadas.update(database_id=database_id, desde=desde, maximo=maximo)
        return [
            {**_normalizar_pagina(PAGINA_CRUDA), "id": f"pagina-{i:03d}"}
            for i in range(maximo)
        ]

    monkeypatch.setattr(NotionClient, "tareas", tareas_falsas)

    estado = agente_notion({"database_id": BASE_ID, "proyecto_id": PROYECTO_ID})

    assert adaptador.LIMITE_TAREAS == 20
    assert llamadas["database_id"] == BASE_ID
    assert llamadas["maximo"] == 20
    assert len(estado["evidencias"]) == 20
    assert estado["error"] is None
    assert set(estado["evidencias"][0]) == {
        "fuente", "id_externo", "autor", "fecha", "descripcion",
        "proyecto_id", "estado", "fecha_limite",
    }


def test_error_403_se_registra_y_no_crea_tareas(monkeypatch, caplog):
    monkeypatch.setenv("NOTION_TOKEN", "token-secreto-de-prueba")

    def tareas_rechazadas(self, database_id, desde=None, maximo=None):
        raise NotionAuthError("Notion rechazó el acceso (HTTP 403) en /databases/x.")

    monkeypatch.setattr(NotionClient, "tareas", tareas_rechazadas)

    with caplog.at_level(logging.ERROR):
        estado = agente_notion({"database_id": BASE_ID, "proyecto_id": PROYECTO_ID})

    assert estado["evidencias"] == []
    assert "Integración fallida: Notion" in estado["error"]
    assert "403" in estado["error"]
    assert "token-secreto-de-prueba" not in estado["error"]
    assert "403" in caplog.text


def test_sin_token_lanza_error_de_acceso(monkeypatch):
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.setattr(
        "app.modulos.evidencias.adaptadores.notion.adaptador.cargar_config",
        lambda: {"token": "", "database_id": ""},
    )

    estado = agente_notion({"database_id": BASE_ID, "proyecto_id": PROYECTO_ID})

    assert estado["evidencias"] == []
    assert "NOTION_TOKEN" in estado["error"]


def test_cliente_pagina_con_next_cursor_y_respeta_el_maximo(monkeypatch):
    cliente = NotionClient(token="x")
    respuestas = iter([
        {"data_sources": [{"id": "ds-1"}]},
        {"results": [PAGINA_CRUDA], "has_more": True, "next_cursor": "c1"},
        {"results": [PAGINA_SIN_RESPONSABLE, PAGINA_CRUDA], "has_more": False},
    ])
    monkeypatch.setattr(cliente, "_request", lambda *a, **k: next(respuestas))

    tareas = cliente.tareas(BASE_ID, maximo=3)

    assert [t["id"] for t in tareas] == ["pagina-001", "pagina-002", "pagina-001"]


def test_cliente_convierte_http_403_en_error_de_acceso(monkeypatch):
    import io
    import urllib.error

    def urlopen_403(*args, **kwargs):
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr("urllib.request.urlopen", urlopen_403)

    try:
        NotionClient(token="secreto").data_source_id(BASE_ID)
        assert False, "debía lanzar NotionAuthError"
    except NotionAuthError as error:
        assert "403" in str(error)
        assert "secreto" not in str(error)
