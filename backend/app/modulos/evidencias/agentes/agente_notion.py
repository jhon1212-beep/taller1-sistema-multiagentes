# -*- coding: utf-8 -*-
"""TA-007 · Agente Notion: nodo de LangGraph.

Orquesta FuenteEvidenciaNotion y, si Notion rechaza el acceso (401/403) o
falla, registra el error y devuelve cero evidencias: nunca inventa tareas.
"""
from __future__ import annotations

import logging
from typing import TypedDict

from app.modulos.evidencias.adaptadores.notion.adaptador import FuenteEvidenciaNotion
from app.modulos.evidencias.adaptadores.notion.cliente import NotionAuthError, NotionError

logger = logging.getLogger(__name__)


class EstadoAgenteNotion(TypedDict, total=False):
    database_id: str
    proyecto_id: int
    desde: str | None
    evidencias: list[dict]
    error: str | None


def agente_notion(estado: EstadoAgenteNotion) -> EstadoAgenteNotion:
    """Nodo de LangGraph: pide las tareas al adaptador y maneja sus fallos."""
    adaptador = FuenteEvidenciaNotion()
    try:
        evidencias = adaptador.obtener_evidencias(
            estado["database_id"], estado["proyecto_id"], desde=estado.get("desde")
        )
    except NotionAuthError as error:
        logger.error("Integración fallida: Notion (acceso rechazado). %s", error)
        return {"evidencias": [], "error": f"Integración fallida: Notion. {error}"}
    except NotionError as error:
        logger.error("Integración fallida: Notion. %s", error)
        return {"evidencias": [], "error": f"Integración fallida: Notion. {error}"}
    return {"evidencias": [e.to_dict() for e in evidencias], "error": None}


def construir_grafo():
    """Grafo mínimo con el nodo del Agente Notion (TA-007)."""
    from langgraph.graph import END, START, StateGraph

    grafo = StateGraph(EstadoAgenteNotion)
    grafo.add_node("agente_notion", agente_notion)
    grafo.add_edge(START, "agente_notion")
    grafo.add_edge("agente_notion", END)
    return grafo.compile()


if __name__ == "__main__":
    import json
    import os

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    base = os.environ.get("NOTION_DATABASE_ID", "")
    resultado = construir_grafo().invoke({"database_id": base, "proyecto_id": 1})
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
