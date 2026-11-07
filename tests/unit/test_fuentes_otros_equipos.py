"""Los agentes leen el Notion y el Drive de cualquier equipo, no solo el nuestro.

- Notion: columnas con otros nombres (plantilla en inglés) y estados equivalentes.
- Drive: documentos dentro de subcarpetas y en unidades compartidas.
- Repositorio SQL: un estado desconocido no tumba el corte (CHECK de TA-004).
"""
import pytest

pytest.importorskip("google.auth")

from app.modulos.evidencias.adaptadores.drive.cliente import (  # noqa: E402
    TIPO_CARPETA,
    DriveClient,
)
from app.modulos.evidencias.adaptadores.notion.cliente import (  # noqa: E402
    _normalizar_pagina,
    normalizar_estado,
)
from app.modulos.supervision.adaptadores.sql import _valid_state  # noqa: E402

PAGINA_PLANTILLA_INGLES = {
    "id": "pagina-en-1",
    "last_edited_time": "2026-10-20T15:00:00.000Z",
    "properties": {
        "Name": {"type": "title", "title": [{"plain_text": "Diseñar login"}]},
        "Assignee": {"type": "people", "people": [{"name": "Ana"}, {"name": "Luis"}]},
        "Status": {"type": "status", "status": {"name": "In progress"}},
        "Due": {"type": "date", "date": {"start": "2026-10-25"}},
        "Created": {"type": "created_time", "created_time": "2026-10-01T00:00:00.000Z"},
    },
}


def test_notion_lee_la_plantilla_en_ingles():
    tarea = _normalizar_pagina(PAGINA_PLANTILLA_INGLES)
    assert tarea == {
        "id": "pagina-en-1",
        "tarea": "Diseñar login",
        "responsable": "Ana, Luis",
        "estado": "En curso",
        "fecha_limite": "2026-10-25",
        "editada": "2026-10-20T15:00:00.000Z",
    }


def test_notion_acepta_estado_de_tipo_select_y_columnas_con_otro_nombre():
    pagina = {
        "id": "p2",
        "last_edited_time": "2026-10-20T15:00:00.000Z",
        "properties": {
            "Actividad": {"type": "title", "title": [{"plain_text": "Informe"}]},
            "Encargado": {"type": "people", "people": []},
            "Estatus": {"type": "select", "select": {"name": "Completado"}},
            "Fecha de entrega": {"type": "date", "date": None},
        },
    }
    tarea = _normalizar_pagina(pagina)
    assert (tarea["tarea"], tarea["responsable"], tarea["estado"], tarea["fecha_limite"]) == (
        "Informe", None, "Listo", None)


@pytest.mark.parametrize("crudo, esperado", [
    ("Listo", "Listo"), ("Done", "Listo"), ("Completed", "Listo"), ("Terminado", "Listo"),
    ("En curso", "En curso"), ("In progress", "En curso"), ("En revisión", "En curso"),
    ("Sin empezar", "Sin empezar"), ("Not started", "Sin empezar"), ("Por hacer", "Sin empezar"),
    ("To-do", "Sin empezar"), ("Bloqueado", None), ("", None), (None, None),
])
def test_estados_equivalentes(crudo, esperado):
    assert normalizar_estado(crudo) == esperado


class _Respuesta:
    def __init__(self, cuerpo):
        self.status_code, self._cuerpo = 200, cuerpo

    def json(self):
        return self._cuerpo


class _SesionFalsa:
    """Simula files.list: raíz -> 2 documentos + subcarpeta (con 2 páginas) -> sub-subcarpeta."""

    def __init__(self):
        self.consultas = []
        self.hijos = {
            "raiz": [
                [_doc("a", "2026-10-01T10:00:00Z"), _carpeta("sub"), _doc("b", "2026-10-05T10:00:00Z")],
            ],
            "sub": [
                [_doc("c", "2026-10-20T10:00:00Z")],
                [_doc("d", "2026-10-03T10:00:00Z"), _carpeta("subsub"), _carpeta("raiz")],  # ciclo
            ],
            "subsub": [[_doc("e", "2026-10-10T10:00:00Z")]],
        }

    def get(self, url, params, timeout):
        self.consultas.append(dict(params))
        carpeta = params["q"].split("'")[1]
        paginas = self.hijos[carpeta]
        pagina = int(params.get("pageToken", 0))
        cuerpo = {"files": paginas[pagina]}
        if pagina + 1 < len(paginas):
            cuerpo["nextPageToken"] = str(pagina + 1)
        return _Respuesta(cuerpo)


def _doc(nombre, fecha):
    return {"id": nombre, "name": nombre, "mimeType": "application/pdf", "modifiedTime": fecha,
            "lastModifyingUser": {"displayName": "Ana"}}


def _carpeta(nombre):
    return {"id": nombre, "name": nombre, "mimeType": TIPO_CARPETA, "modifiedTime": "2026-10-30T00:00:00Z"}


def test_drive_recorre_subcarpetas_sin_contar_carpetas_ni_repetir():
    cliente = DriveClient("{}")
    sesion = _SesionFalsa()
    cliente._sesion = sesion

    archivos = cliente.archivos_de_carpeta("raiz")

    assert [a["nombre"] for a in archivos] == ["c", "e", "b", "d", "a"]  # del más reciente al más antiguo
    assert all(c["supportsAllDrives"] == "true" for c in sesion.consultas)
    assert len(sesion.consultas) == 4  # raíz, sub (2 páginas) y subsub; el ciclo no se repite


def test_drive_respeta_el_maximo():
    cliente = DriveClient("{}")
    cliente._sesion = _SesionFalsa()
    assert [a["nombre"] for a in cliente.archivos_de_carpeta("raiz", maximo=2)] == ["c", "e"]


def test_estado_desconocido_se_guarda_vacio():
    assert [_valid_state(e) for e in ("Listo", "En curso", "Sin empezar", "Done", None)] == [
        "Listo", "En curso", "Sin empezar", None, None]


def test_notion_usa_el_token_del_equipo_si_su_base_esta_en_otro_espacio(monkeypatch):
    from app.modulos.evidencias.adaptadores.notion.cliente import token_para_base

    monkeypatch.setenv("NOTION_TOKEN", "token-del-grupo-8")
    monkeypatch.setenv("NOTION_TOKENS", '{"3ea2ed0d-a4c3-803f-9191-c8cda25669d4": "token-del-otro-equipo"}')
    assert token_para_base("3ea2ed0da4c3803f9191c8cda25669d4") == "token-del-otro-equipo"
    assert token_para_base("ffffffffffffffffffffffffffffffff") == "token-del-grupo-8"

    monkeypatch.delenv("NOTION_TOKENS")
    assert token_para_base("3ea2ed0da4c3803f9191c8cda25669d4") == "token-del-grupo-8"
