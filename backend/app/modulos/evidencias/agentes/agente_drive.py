# -*- coding: utf-8 -*-
"""TA-014 · Agente Drive: nodo de LangGraph.

Si Drive falla, guarda el error en el estado en vez de interrumpir el grafo.
"""
from __future__ import annotations

from typing import TypedDict

from app.modulos.evidencias.adaptadores.drive.adaptador import FuenteEvidenciaDrive
from app.modulos.evidencias.adaptadores.drive.cliente import DriveError


class EstadoAgenteDrive(TypedDict, total=False):
    carpeta_id: str
    proyecto_id: int
    evidencias: list[dict]
    estado_fuente: str  # "ok" | "fallo"
    error: str | None


def agente_drive(estado: EstadoAgenteDrive) -> EstadoAgenteDrive:
    try:
        evidencias = FuenteEvidenciaDrive().obtener_evidencias(
            estado["carpeta_id"], estado["proyecto_id"]
        )
    except DriveError as error:
        return {"evidencias": [], "estado_fuente": "fallo", "error": str(error)}
    return {
        "evidencias": [e.to_dict() for e in evidencias],
        "estado_fuente": "ok",
        "error": None,
    }


def construir_grafo():
    from langgraph.graph import END, START, StateGraph

    grafo = StateGraph(EstadoAgenteDrive)
    grafo.add_node("agente_drive", agente_drive)
    grafo.add_edge(START, "agente_drive")
    grafo.add_edge("agente_drive", END)
    return grafo.compile()


if __name__ == "__main__":
    import json
    import os

    carpeta = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    resultado = construir_grafo().invoke({"carpeta_id": carpeta, "proyecto_id": 1})
    print(json.dumps(resultado, ensure_ascii=False, indent=2))