# -*- coding: utf-8 -*-
"""TA-006 · Pruebas del Agente GitHub.

No llaman a la API real: simulan GitHubClient para que la prueba sea rápida,
determinista y no dependa de un GITHUB_TOKEN. La verificación contra la API
real ("5 de 5 commits coinciden") es un paso manual aparte, documentado en
docs/sprint1/TA-006.md.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from scripts.github_client import GitHubClient, GitHubError  # noqa: E402

from app.agentes.nodo_github import (  # noqa: E402
    LIMITE_COMMITS,
    agente_github,
    normalizar_commit,
)

COMMIT_CRUDO_EJEMPLO = {
    "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9011121314",
    "mensaje": "TA-006: nodo del agente GitHub",
    "autor": "jhon1212-beep",
    "fecha": "2026-10-01T10:00:00Z",
}


def test_normalizar_commit_mapea_los_campos_al_esquema_comun():
    evidencia = normalizar_commit(COMMIT_CRUDO_EJEMPLO)

    assert evidencia.fuente == "github"
    assert evidencia.id_externo == COMMIT_CRUDO_EJEMPLO["sha"]
    assert len(evidencia.id_externo) == 40  # SHA completo, no truncado
    assert evidencia.autor == "jhon1212-beep"
    assert evidencia.descripcion == "TA-006: nodo del agente GitHub"


def test_normalizar_commit_usa_desconocido_si_falta_el_autor():
    crudo = {**COMMIT_CRUDO_EJEMPLO, "autor": None}
    evidencia = normalizar_commit(crudo)
    assert evidencia.autor == "desconocido"


def test_agente_github_pide_como_maximo_20_commits(monkeypatch):
    llamadas = {}

    def commits_detallados_falso(self, repo, desde=None, maximo=None):
        llamadas["repo"] = repo
        llamadas["maximo"] = maximo
        return [dict(COMMIT_CRUDO_EJEMPLO, sha=f"{i:040d}") for i in range(maximo)]

    monkeypatch.setattr(GitHubClient, "commits_detallados", commits_detallados_falso)

    estado = agente_github({"repo": "jhon1212-beep/taller1-sistema-multiagentes"})

    assert llamadas["maximo"] == LIMITE_COMMITS
    assert len(estado["evidencias"]) == LIMITE_COMMITS
    assert estado["error"] is None
    # cada evidencia ya viene normalizada (no el dict crudo del cliente)
    assert set(estado["evidencias"][0]) == {"fuente", "id_externo", "autor", "fecha", "descripcion"}


def test_agente_github_devuelve_error_si_la_api_falla(monkeypatch):
    def commits_detallados_que_falla(self, repo, desde=None, maximo=None):
        raise GitHubError("HTTP 404 al consultar el repositorio")

    monkeypatch.setattr(GitHubClient, "commits_detallados", commits_detallados_que_falla)

    estado = agente_github({"repo": "no-existe/repo-inventado"})

    assert estado["evidencias"] == []
    assert "404" in estado["error"]
