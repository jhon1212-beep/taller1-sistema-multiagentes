"""SP-001: POC de 2 nodos: Agente GitHub (simulado) -> Agente Supervisor (Gemini)."""
import json
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env", override=True)

llm = ChatGoogleGenerativeAI(
    model=os.environ["GEMINI_MODEL"],
    google_api_key=os.environ["GEMINI_API_KEY"],
    temperature=0
)


class Estado(TypedDict, total=False):
    commits: list
    resumen: str
    tokens: dict


def agente_github(estado: Estado) -> Estado:
    # Simulado: en TA-006 se reemplaza por GitHub REST API. Autores ya seudonimizados.
    return {
        "commits": [
            {
                "autor": "Integrante 1",
                "fecha": "2026-09-28",
                "mensaje": "estructura del repositorio",
            },
            {
                "autor": "Integrante 2",
                "fecha": "2026-09-29",
                "mensaje": "modelo de datos inicial",
            },
        ]
    }


def agente_supervisor(estado: Estado) -> Estado:
    lista = "\n".join(
        f"- {c['fecha']} {c['autor']}: {c['mensaje']}"
        for c in estado["commits"]
    )
    r = llm.invoke(
        "Resume en 2 frases el avance del proyecto, sin juzgar a nadie:\n" + lista
    )
    return {
        "resumen": r.text,
        "tokens": dict(r.usage_metadata or {}),
    }


grafo = StateGraph(Estado)
grafo.add_node("agente_github", agente_github)
grafo.add_node("agente_supervisor", agente_supervisor)

grafo.add_edge(START, "agente_github")
grafo.add_edge("agente_github", "agente_supervisor")
grafo.add_edge("agente_supervisor", END)

resultado = grafo.compile().invoke({})

salida = {
    "modelo": os.environ["GEMINI_MODEL"],
    "resumen": resultado["resumen"],
    "tokens": resultado["tokens"],
}

print(json.dumps(salida, ensure_ascii=False, indent=2))

(RAIZ / "docs/sprint1/evidencias/SP-001_poc_salida.json").write_text(
    json.dumps(salida, ensure_ascii=False, indent=2),
    encoding="utf-8",
)