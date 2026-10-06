# -*- coding: utf-8 -*-
"""TA-006: pruebas del adaptador y del agente GitHub.

Simulan el cliente para evitar llamadas a la API real.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BACKEND = RAIZ / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modulos.evidencias.adaptadores.github import adaptador  # noqa: E402
from app.modulos.evidencias.adaptadores.github.cliente import (  # noqa: E402
    GitHubClient,
    GitHubError,
)
from app.modulos.evidencias.agentes.agente_github import (  # noqa: E402
    agente_github,
)

COMMIT_CRUDO_EJEMPLO = {
    "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9011121314",
    "mensaje": "TA-006: nodo del agente GitHub",
    "autor": "jhon1212-beep",
    "fecha": "2026-10-01T10:00:00Z",
}

PROYECTO_ID = 1
REPO = "jhon1212-beep/taller1-sistema-multiagentes"


def test_normalizar_commit_mapea_los_campos_al_esquema_comun():
    evidencia = adaptador._normalizar_commit(
        COMMIT_CRUDO_EJEMPLO, PROYECTO_ID
    )

    assert evidencia.fuente == "github"
    assert evidencia.id_externo == COMMIT_CRUDO_EJEMPLO["sha"]
    assert len(evidencia.id_externo) == 40
    assert evidencia.autor == COMMIT_CRUDO_EJEMPLO["autor"]
    assert evidencia.fecha == COMMIT_CRUDO_EJEMPLO["fecha"]
    assert evidencia.descripcion == COMMIT_CRUDO_EJEMPLO["mensaje"]
    assert evidencia.proyecto_id == PROYECTO_ID


def test_normalizar_commit_usa_desconocido_si_falta_el_autor():
    crudo = {**COMMIT_CRUDO_EJEMPLO, "autor": None}

    evidencia = adaptador._normalizar_commit(crudo, PROYECTO_ID)

    assert evidencia.autor == "desconocido"


def test_agente_github_pide_como_maximo_20_commits(monkeypatch):
    llamadas = {}

    # Evita leer las credenciales locales.
    monkeypatch.setattr(adaptador, "cargar_env", lambda: {})

    def commits_detallados_falso(self, repo, desde=None, maximo=None):
        llamadas["repo"] = repo
        llamadas["desde"] = desde
        llamadas["maximo"] = maximo
        return [
            dict(COMMIT_CRUDO_EJEMPLO, sha=f"{i:040d}")
            for i in range(maximo)
        ]

    monkeypatch.setattr(
        GitHubClient, "commits_detallados", commits_detallados_falso
    )

    estado = agente_github({
        "repo": REPO,
        "proyecto_id": PROYECTO_ID,
        "desde": "2026-10-01T00:00:00Z",
    })

    assert adaptador.LIMITE_COMMITS == 20
    assert llamadas["repo"] == REPO
    assert llamadas["desde"] == "2026-10-01T00:00:00Z"
    assert llamadas["maximo"] == 20
    assert len(estado["evidencias"]) == 20
    assert estado["error"] is None

    assert set(estado["evidencias"][0]) == {
        "fuente",
        "id_externo",
        "autor",
        "fecha",
        "descripcion",
        "proyecto_id",
    }
    assert all(
        evidencia["proyecto_id"] == PROYECTO_ID
        for evidencia in estado["evidencias"]
    )


def test_agente_github_devuelve_error_si_la_api_falla(monkeypatch):
    monkeypatch.setattr(adaptador, "cargar_env", lambda: {})

    def commits_detallados_que_falla(self, repo, desde=None, maximo=None):
        raise GitHubError("HTTP 404 al consultar el repositorio")

    monkeypatch.setattr(
        GitHubClient, "commits_detallados", commits_detallados_que_falla
    )

    estado = agente_github({
        "repo": "no-existe/repo-inventado",
        "proyecto_id": PROYECTO_ID,
    })

    assert estado["evidencias"] == []
    assert "404" in estado["error"]
