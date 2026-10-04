# -*- coding: utf-8 -*-
"""TA-006 · Agente GitHub: nodo de LangGraph.

Orquesta FuenteEvidenciaGitHub (adaptadores/github/adaptador.py) y decide
qué hacer si falla: en vez de interrumpir el programa, guarda el error en
el estado para que el grafo pueda seguir (por ejemplo, con los datos de la
última sincronización).
"""
from __future__ import annotations

from typing import TypedDict

from app.modulos.evidencias.adaptadores.github.adaptador import FuenteEvidenciaGitHub
from app.modulos.evidencias.adaptadores.github.cliente import GitHubError


class EstadoAgenteGitHub(TypedDict, total=False):
    repo: str  # "owner/repo"
    proyecto_id: int
    desde: str | None
    evidencias: list[dict]
    error: str | None


def agente_github(estado: EstadoAgenteGitHub) -> EstadoAgenteGitHub:
    """Nodo de LangGraph: pide evidencias al adaptador y maneja sus fallos."""
    adaptador = FuenteEvidenciaGitHub()
    try:
        evidencias = adaptador.obtener_evidencias(
            estado["repo"], estado["proyecto_id"], desde=estado.get("desde")
        )
    except GitHubError as error:
        return {"evidencias": [], "error": str(error)}
    return {"evidencias": [e.to_dict() for e in evidencias], "error": None}


def construir_grafo():
    """Arma el grafo con el nodo del Agente GitHub (TA-006).

    Se amplía en tareas futuras con los nodos de Notion y Drive, y con el
    Agente Supervisor (módulo supervision, de Reyes), según el Product
    Backlog v6.0.
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
    resultado = construir_grafo().invoke({"repo": repo, "proyecto_id": 1})
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
