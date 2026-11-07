import logging
import pytest
pytest.importorskip("langgraph")
from langsmith import tracing_context

from app.modulos.evidencias.adaptadores.compuesta import FuenteEvidenciaCompuesta
from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa
from app.modulos.supervision.grafo.construir_grafo import construir_grafo
from app.modulos.supervision.grafo.estado import crear_estado_inicial

REFS = {"github": "repo-demo", "notion": "base-demo", "drive": "carpeta-demo"}


class FuenteQueFalla:
    def __init__(self, mensaje):
        self.mensaje = mensaje

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        raise RuntimeError(self.mensaje)


def _correr(fuentes):
    with tracing_context(enabled=False):
        grafo = construir_grafo(FuenteEvidenciaCompuesta(fuentes), REFS)
        return grafo.invoke(crear_estado_inicial(1, "2026-10-06T00:00:00Z"))


def test_cp16_github_caido_queda_en_fallo(caplog):
    falsa = FuenteEvidenciaFalsa()
    caplog.set_level(logging.ERROR, logger="evidencias")
    r = _correr({
        "repo-demo": FuenteQueFalla("HTTP 404 al consultar el repositorio"),
        "base-demo": falsa, "carpeta-demo": falsa,
    })
    assert r["estado_fuentes"]["github"] == "fallo"
    assert all(e.fuente != "github" for e in r["evidencias"])
    assert "repo-demo" in caplog.text


def test_cp08_token_de_notion_invalido_queda_en_fallo(caplog):
    falsa = FuenteEvidenciaFalsa()
    caplog.set_level(logging.ERROR, logger="evidencias")
    r = _correr({
        "repo-demo": falsa,
        "base-demo": FuenteQueFalla("HTTP 401 token invalido"),
        "carpeta-demo": falsa,
    })
    assert r["estado_fuentes"]["notion"] == "fallo"
    assert all(e.fuente != "notion" for e in r["evidencias"])