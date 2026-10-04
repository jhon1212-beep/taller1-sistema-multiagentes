# -*- coding: utf-8 -*-
"""TA-006 · Agente GitHub: nodo de LangGraph que extrae y normaliza commits.

Reutiliza el cliente de solo lectura de EN-001 (scripts/github_client.py).
Normaliza cada commit al esquema común de evidencia (ver docs/modelo-de-datos.md
y docs/arquitectura.md): fuente, id_externo, autor, fecha, descripcion.

Este nodo es el primero del grafo de agentes. Los siguientes (Notion, Drive,
cálculo de indicadores) se agregan en tareas posteriores siguiendo el mismo
contrato: un nodo recibe un estado y devuelve el estado actualizado.
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypedDict

# Repositorio: backend/app/agentes/nodo_github.py -> sube 3 niveles hasta la raíz
RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from scripts.github_client import GitHubClient, GitHubError, cargar_env  # noqa: E402

LIMITE_COMMITS = 20  # Criterio de aceptación de TA-006: hasta 20 commits


@dataclass
class EvidenciaNormalizada:
    """Esquema común de evidencia (TA-010), aplicado a un commit de GitHub."""

    fuente: str
    id_externo: str  # SHA completo del commit: identificador único
    autor: str
    fecha: str | None
    descripcion: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalizar_commit(commit_crudo: dict) -> EvidenciaNormalizada:
    """Convierte un commit crudo (de GitHubClient.commits_detallados) al
    esquema común de evidencia."""
    return EvidenciaNormalizada(
        fuente="github",
        id_externo=commit_crudo["sha"],
        autor=commit_crudo.get("autor") or "desconocido",
        fecha=commit_crudo.get("fecha"),
        descripcion=commit_crudo.get("mensaje") or "",
    )


class EstadoAgenteGitHub(TypedDict, total=False):
    repo: str  # "owner/repo", por ejemplo "jhon1212-beep/taller1-sistema-multiagentes"
    desde: str | None  # fecha ISO opcional, para no repetir todo el historial
    evidencias: list[dict]
    error: str | None


def agente_github(estado: EstadoAgenteGitHub) -> EstadoAgenteGitHub:
    """Nodo de LangGraph: extrae hasta 20 commits y los normaliza (TA-006)."""
    env = cargar_env()
    cliente = GitHubClient(token=env.get("GITHUB_TOKEN"), org=env.get("GITHUB_ORG"))
    try:
        crudos = cliente.commits_detallados(
            estado["repo"], desde=estado.get("desde"), maximo=LIMITE_COMMITS
        )
    except GitHubError as error:
        return {"evidencias": [], "error": str(error)}

    evidencias = [normalizar_commit(c).to_dict() for c in crudos]
    return {"evidencias": evidencias, "error": None}


def construir_grafo():
    """Arma el grafo con el nodo del Agente GitHub (TA-006).

    Se amplía en tareas futuras agregando los nodos de Notion, Drive y
    cálculo de indicadores, tal como quedó definido en docs/arquitectura.md.
    """
    from langgraph.graph import END, START, StateGraph

    grafo = StateGraph(EstadoAgenteGitHub)
    grafo.add_node("agente_github", agente_github)
    grafo.add_edge(START, "agente_github")
    grafo.add_edge("agente_github", END)
    return grafo.compile()


if __name__ == "__main__":
    import json
    import os

    repo = os.environ.get("TA006_REPO", "jhon1212-beep/taller1-sistema-multiagentes")
    resultado = construir_grafo().invoke({"repo": repo})
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
