"""TA-015: Agente Supervisor para la orquestación de fuentes de evidencia."""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, Callable, Mapping, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.evidencias.puertos import FuenteEvidencia
from app.modulos.supervision.dominio import (
    Alerta,
    EstadoFuente,
    Fuente,
    Indicadores,
)
from app.modulos.supervision.grafo.estado import crear_estado_inicial
from app.modulos.supervision.motor_indicadores import evaluar as evaluate_indicators

EVALUATE_NODE = "evaluate"

# La evaluación se ejecuta después de consolidar las evidencias.
def evaluate(state: SupervisorState) -> dict:
    result = run_engine(state.get("evidencias") or [], state["fecha_corte"])
    failed = {source for source, status in state["estado_fuentes"].items()
              if status == "fallo"}
    alerts = [dict(alert) for alert in result["alertas"]
              if alert["fuente"] not in failed]
    return {"indicadores": dict(result["indicadores"]), "alertas": alerts}

# Nueva ruta: consolidate -> evaluate -> END.


# Bloque A. Imports y constantes

SOURCES: tuple[Fuente, ...] = ("github", "notion", "drive")

SUPERVISOR_NODE = "supervisor"
CONSOLIDATE_NODE = "consolidate"
EVALUATE_NODE = "evaluate"

Engine = Callable[[list[Evidencia], str], Mapping[str, Any]]

AGENT_NODES: dict[Fuente, str] = {
    "github": "github_agent",
    "notion": "notion_agent",
    "drive": "drive_agent",
}

NO_ADAPTER_ERROR = "Sin adaptador configurado para esta fuente."
NO_REFERENCE_ERROR = "El proyecto no tiene referencia registrada para esta fuente."


# Bloque B. Estado del grafo con reductores

def merge_dicts(current: dict, update: dict) -> dict:
    """Reductor: combina los resultados que cada agente escribe en paralelo."""
    return {**current, **update}


class SupervisorState(TypedDict):
    """Estado interno del Agente Supervisor.

    Las claves en español son las del contrato EstadoSupervision (AR-02).
    ``raw_evidence`` y ``source_details`` son internas: los agentes escriben
    en ellas en paralelo, por eso usan reductores.
    """

    proyecto_id: int
    fecha_corte: str
    referencias: dict[Fuente, str]
    evidencias: list[Evidencia]
    estado_fuentes: Annotated[dict[Fuente, EstadoFuente], merge_dicts]
    errores_fuentes: Annotated[dict[Fuente, str | None], merge_dicts]
    indicadores: Indicadores
    alertas: list[Alerta]
    raw_evidence: Annotated[list[Evidencia], operator.add]
    source_details: Annotated[dict[Fuente, dict[str, int]], merge_dicts]


class AgentTask(TypedDict):
    """Encargo que el supervisor envía a un agente de fuente."""

    source: Fuente
    reference: str
    proyecto_id: int
    fecha_corte: str


# Bloque C. Fecha de corte

def parse_cutoff(value: str) -> datetime:
    """Convierte una fecha ISO 8601 con zona horaria a UTC.

    Lanza ValueError si el formato no es válido o si falta la zona horaria,
    con el mismo criterio que RepositorioSupervisionMemoria (AR-02).
    """
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ValueError(
            f"Fecha de corte no válida: {value!r}. Usa ISO 8601 con zona horaria."
        ) from error

    if parsed.tzinfo is None:
        raise ValueError("La fecha de corte debe incluir zona horaria.")

    return parsed.astimezone(timezone.utc)


def is_within_cutoff(evidence: Evidencia, cutoff: datetime) -> bool:
    """True si la evidencia ocurrió hasta la fecha de corte.

    Una evidencia sin fecha se conserva: no se puede afirmar que sea
    posterior al corte. Una fecha ilegible se trata como fuera de corte.
    """
    if not evidence.fecha:
        return True

    try:
        moment = datetime.fromisoformat(
            evidence.fecha.replace("Z", "+00:00")
        )
    except ValueError:
        return False

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    return moment.astimezone(timezone.utc) <= cutoff


def _sort_key(evidence: Evidencia) -> tuple[int, str]:
    # Primero las que tienen fecha; al final quedan las evidencias sin fecha.
    return (1, evidence.fecha) if evidence.fecha else (0, "")


# Bloque D. Entrada del grafo

def build_supervisor_input(
    project_id: int,
    cutoff: str,
    references: Mapping[Fuente, str],
) -> dict[str, Any]:
    """Arma la entrada del grafo a partir del estado inicial de AR-02."""
    parse_cutoff(cutoff)

    initial = crear_estado_inicial(project_id, cutoff)

    return {
        **initial,
        "referencias": {
            source: references[source]
            for source in SOURCES
            if references.get(source)
        },
    }


# Bloques E-J. Construcción del grafo

def build_supervisor_graph(
    adapters: Mapping[Fuente, FuenteEvidencia],
    engine: Engine | None = None,
):
    """Construye el Supervisor con evaluación determinista de evidencias."""
    run_engine = engine if engine is not None else evaluate_indicators

    # Bloque E. Qué fuentes se pueden consultar
    local_adapters = {
        source: adapters[source]
        for source in SOURCES
        if adapters.get(source) is not None
    }

    def plan_sources(state: SupervisorState) -> list[Fuente]:
        references = state.get("referencias") or {}

        return [
            source
            for source in SOURCES
            if source in local_adapters and references.get(source)
        ]

    # Bloque F. Nodo supervisor
    def supervisor(state: SupervisorState) -> dict:
        """Valida el corte y marca como fallo las fuentes no consultables."""
        parse_cutoff(state["fecha_corte"])

        planned = plan_sources(state)
        references = state.get("referencias") or {}

        statuses: dict[Fuente, EstadoFuente] = {}
        errors: dict[Fuente, str | None] = {}

        for source in SOURCES:
            if source in planned:
                statuses[source] = "pendiente"
                errors[source] = None

            elif source not in local_adapters:
                statuses[source] = "fallo"
                errors[source] = NO_ADAPTER_ERROR

            elif not references.get(source):
                statuses[source] = "fallo"
                errors[source] = NO_REFERENCE_ERROR

        return {
            "estado_fuentes": statuses,
            "errores_fuentes": errors,
        }

    # Bloque G. Reparto en paralelo con Send
    def dispatch(state: SupervisorState):
        """Envía un encargo a cada agente planificado en paralelo."""
        planned = plan_sources(state)

        if not planned:
            return CONSOLIDATE_NODE

        return [
            Send(
                AGENT_NODES[source],
                {
                    "source": source,
                    "reference": state["referencias"][source],
                    "proyecto_id": state["proyecto_id"],
                    "fecha_corte": state["fecha_corte"],
                },
            )
            for source in planned
        ]

    # Bloque H. Agente de fuente
    def make_agent(source: Fuente):
        adapter = local_adapters.get(source)

        def source_agent(task: AgentTask) -> dict:
            """Consulta el adaptador de la fuente y aplica el corte."""
            cutoff = parse_cutoff(task["fecha_corte"])

            try:
                fetched = adapter.obtener_evidencias(
                    referencia=task["reference"],
                    proyecto_id=task["proyecto_id"],
                )

            except Exception as error:
                # Una fuente caída no debe detener a las demás.
                return {
                    "estado_fuentes": {source: "fallo"},
                    "errores_fuentes": {
                        source: f"{type(error).__name__}: {error}"
                    },
                    "source_details": {
                        source: {
                            "evidencias": 0,
                            "fuera_de_corte": 0,
                        }
                    },
                }

            own = [
                evidence
                for evidence in fetched
                if evidence.fuente == source
                and evidence.proyecto_id == task["proyecto_id"]
            ]

            kept = [
                evidence
                for evidence in own
                if is_within_cutoff(evidence, cutoff)
            ]

            return {
                "raw_evidence": kept,
                "estado_fuentes": {source: "ok"},
                "errores_fuentes": {source: None},
                "source_details": {
                    source: {
                        "evidencias": len(kept),
                        "fuera_de_corte": len(own) - len(kept),
                    }
                },
            }

        source_agent.__name__ = AGENT_NODES[source]

        return source_agent

    # Bloque I. Consolidación
    def consolidate(state: SupervisorState) -> dict:
        """Une evidencias sin duplicados y las ordena por fecha."""
        unique: dict[tuple[str, str], Evidencia] = {}

        for evidence in state.get("raw_evidence") or []:
            unique[
                (evidence.fuente, evidence.id_externo)
            ] = evidence

        ordered = sorted(
            unique.values(),
            key=_sort_key,
            reverse=True,
        )

        return {"evidencias": ordered}

    # Bloque I2. Calcular los indicadores y reglas sin LLM.
    def evaluate(state: SupervisorState) -> dict:
        """Evalúa las evidencias consolidadas sin inferir actividad faltante."""
        result = run_engine(state.get("evidencias") or [], state["fecha_corte"])
        failed = {
            source
            for source, status in (state.get("estado_fuentes") or {}).items()
            if status == "fallo"
        }
        alerts = [
            dict(alert) for alert in result["alertas"]
            if alert["fuente"] not in failed
        ]
        return {"indicadores": dict(result["indicadores"]), "alertas": alerts}

    # Bloque J. Armado del grafo
    graph = StateGraph(SupervisorState)

    graph.add_node(
        SUPERVISOR_NODE,
        supervisor,
    )

    for source in SOURCES:
        if source in local_adapters:
            graph.add_node(
                AGENT_NODES[source],
                make_agent(source),
            )

            graph.add_edge(
                AGENT_NODES[source],
                CONSOLIDATE_NODE,
            )

    graph.add_node(
        CONSOLIDATE_NODE,
        consolidate,
    )

    graph.add_edge(
        START,
        SUPERVISOR_NODE,
    )

    graph.add_conditional_edges(
        SUPERVISOR_NODE,
        dispatch,
        [
            AGENT_NODES[source]
            for source in SOURCES
            if source in local_adapters
        ]
        + [CONSOLIDATE_NODE],
    )

    graph.add_node(EVALUATE_NODE, evaluate)

    graph.add_edge(CONSOLIDATE_NODE, EVALUATE_NODE)
    graph.add_edge(EVALUATE_NODE, END)

    return graph.compile()


# Bloque K. Salida en JSON

def to_consolidated_report(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Convierte el estado final en el consolidado por proyecto."""
    details = state.get("source_details") or {}
    evidences = state.get("evidencias") or []

    sources = {
        source: {
            "estado": state["estado_fuentes"].get(
                source,
                "fallo",
            ),
            "error": state["errores_fuentes"].get(source),
            "evidencias": details.get(
                source,
                {},
            ).get("evidencias", 0),
            "fuera_de_corte": details.get(
                source,
                {},
            ).get("fuera_de_corte", 0),
        }
        for source in SOURCES
    }

    return {
        "proyecto_id": state["proyecto_id"],
        "fecha_corte": state["fecha_corte"],
        "fuentes": sources,
        "total_evidencias": len(evidences),
        "evidencias": [
            evidence.to_dict()
            for evidence in evidences
        ],
        "indicadores": dict(state["indicadores"]),
        "alertas": list(state["alertas"]),
    }