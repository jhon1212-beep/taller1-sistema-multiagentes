"""TA-015: pruebas de integración del Agente Supervisor (grafo completo)."""

import pytest

# Estas pruebas requieren LangGraph y LangSmith.
# Si alguna dependencia no está instalada, pytest omite este archivo
# en lugar de generar un error de importación.
pytest.importorskip("langgraph")
pytest.importorskip("langsmith")

from langsmith import tracing_context

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.supervision.grafo.supervisor import (
    AGENT_NODES,
    NO_ADAPTER_ERROR,
    NO_REFERENCE_ERROR,
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)


# Fecha de corte común para todos los escenarios de integración.
# Incluye zona horaria porque TA-015 exige fechas ISO 8601 con timezone.
CUTOFF = "2026-10-12T23:59:59-05:00"

# Referencias de prueba para cada una de las tres fuentes.
REFERENCES = {
    "github": "owner/repo",
    "notion": "base-demo",
    "drive": "carpeta-demo",
}


class RecordingSource:
    """Adaptador de prueba que devuelve evidencias fijas y registra sus llamadas.

    Permite comprobar no solo el resultado del grafo, sino también si cada
    agente fue invocado con la referencia y el proyecto correctos.
    """

    def __init__(self, evidences=None, error=None):
        self.evidences = evidences or []
        self.error = error
        self.calls = []

    def obtener_evidencias(
        self,
        referencia,
        proyecto_id,
        *,
        limite=None,
        desde=None,
    ):
        # Registramos la llamada para verificar después qué agente
        # fue consultado y con qué parámetros.
        self.calls.append((referencia, proyecto_id))

        # Permite simular la caída de una fuente externa.
        if self.error:
            raise self.error

        # Se devuelve una copia para evitar modificar accidentalmente
        # la lista interna del adaptador durante la ejecución.
        return list(self.evidences)


def ev(fuente, id_externo, fecha, proyecto_id=1):
    """Crea una evidencia mínima para los escenarios de integración."""
    return Evidencia(
        fuente,
        id_externo,
        "autor-demo",
        fecha,
        f"{fuente} {id_externo}",
        proyecto_id,
    )


@pytest.fixture(autouse=True)
def disable_tracing():
    """Evita enviar trazas reales a LangSmith durante las pruebas."""
    with tracing_context(enabled=False):
        yield


@pytest.fixture
def adapters():
    """Construye tres adaptadores de prueba con una evidencia válida cada uno."""
    return {
        "github": RecordingSource(
            [ev("github", "sha-1", "2026-10-10T15:00:00Z")]
        ),
        "notion": RecordingSource(
            [ev("notion", "tarea-1", "2026-10-09T12:00:00Z")]
        ),
        "drive": RecordingSource(
            [ev("drive", "doc-1", "2026-10-08T09:00:00Z")]
        ),
    }


def run(
    adapters,
    references=REFERENCES,
    cutoff=CUTOFF,
    project_id=1,
):
    """Construye e invoca el grafo completo del Supervisor.

    Esta función evita repetir el mismo proceso en cada prueba:
    crear el grafo, preparar la entrada inicial y ejecutar LangGraph.
    """
    graph = build_supervisor_graph(adapters)

    supervisor_input = build_supervisor_input(
        project_id,
        cutoff,
        references,
    )

    return graph.invoke(supervisor_input)


def test_graph_follows_supervisor_pattern():
    """Verifica que el grafo respete el patrón supervisor jerárquico."""

    graph = build_supervisor_graph(
        {
            "github": RecordingSource(),
            "notion": RecordingSource(),
            "drive": RecordingSource(),
        }
    )

    nodes = set(graph.get_graph().nodes)

    # El grafo debe contener un Supervisor central,
    # los tres agentes de fuente y el nodo final de consolidación.
    assert {
        "supervisor",
        "consolidate",
        *AGENT_NODES.values(),
    } <= nodes


def test_cp10_invokes_three_agents_and_returns_one_consolidated_ok(adapters):
    """Comprueba el escenario normal con las tres fuentes disponibles."""

    final = run(adapters)
    report = to_consolidated_report(final)

    # Cada fuente debe ser consultada una sola vez
    # con su referencia correspondiente y el proyecto 1.
    for source, adapter in adapters.items():
        assert adapter.calls == [
            (REFERENCES[source], 1)
        ]

    # En el escenario normal las tres fuentes deben terminar correctamente.
    assert final["estado_fuentes"] == {
        "github": "ok",
        "notion": "ok",
        "drive": "ok",
    }

    assert all(
        error is None
        for error in final["errores_fuentes"].values()
    )

    # El Supervisor debe devolver un único consolidado
    # correspondiente al proyecto y fecha de corte utilizados.
    assert report["proyecto_id"] == 1
    assert report["fecha_corte"] == CUTOFF
    assert report["total_evidencias"] == 3

    # Las evidencias finales deben incluir una por cada fuente.
    assert [
        e["fuente"]
        for e in report["evidencias"]
    ] == [
        "github",
        "notion",
        "drive",
    ]


def test_cutoff_discards_later_evidence_and_counts_it(adapters):
    """Verifica el filtrado de evidencias posteriores a la fecha de corte."""

    # Se agrega una evidencia posterior al corte para comprobar
    # que el Supervisor la descarte.
    adapters["github"].evidences.append(
        ev(
            "github",
            "sha-futuro",
            "2026-10-13T05:00:01Z",
        )
    )

    report = to_consolidated_report(
        run(adapters)
    )

    ids = {
        e["id_externo"]
        for e in report["evidencias"]
    }

    # La evidencia posterior al corte no debe llegar al consolidado.
    assert "sha-futuro" not in ids

    # Aunque se descarte, debe contabilizarse en fuera_de_corte.
    assert report["fuentes"]["github"] == {
        "estado": "ok",
        "error": None,
        "evidencias": 1,
        "fuera_de_corte": 1,
    }


def test_failed_source_is_marked_and_others_continue(adapters):
    """Comprueba que el fallo de una fuente no detenga a las demás."""

    # Simulamos una caída de Notion.
    adapters["notion"] = RecordingSource(
        error=ConnectionError("Notion no responde")
    )

    final = run(adapters)

    # Solo Notion debe quedar en fallo.
    assert final["estado_fuentes"] == {
        "github": "ok",
        "notion": "fallo",
        "drive": "ok",
    }

    # El error debe conservar el tipo y el detalle de la excepción.
    assert final["errores_fuentes"]["notion"] == (
        "ConnectionError: Notion no responde"
    )

    # GitHub y Drive deben continuar y aportar sus evidencias.
    assert {
        e.fuente
        for e in final["evidencias"]
    } == {
        "github",
        "drive",
    }


def test_source_without_adapter_or_reference_fails_without_being_called(adapters):
    """Verifica fuentes incompletas por falta de adaptador o referencia."""

    # Drive no tendrá referencia.
    references = {
        "github": "owner/repo",
        "notion": "base-demo",
    }

    drive = adapters["drive"]

    # Notion no tendrá adaptador.
    adapters_without_notion = {
        "github": adapters["github"],
        "drive": drive,
    }

    final = run(
        adapters_without_notion,
        references=references,
    )

    # GitHub puede ejecutarse; Notion y Drive deben quedar en fallo.
    assert final["estado_fuentes"] == {
        "github": "ok",
        "notion": "fallo",
        "drive": "fallo",
    }

    # Se distingue claramente la causa de cada fallo.
    assert (
        final["errores_fuentes"]["notion"]
        == NO_ADAPTER_ERROR
    )
    assert (
        final["errores_fuentes"]["drive"]
        == NO_REFERENCE_ERROR
    )

    # Drive no debe ser invocado si no tiene referencia.
    assert drive.calls == []


def test_no_source_remains_pending_even_without_any_adapter():
    """Comprueba que ninguna fuente termine en estado pendiente."""

    # Se ejecuta el Supervisor sin ningún adaptador disponible.
    final = run({})

    # Las tres fuentes deben terminar explícitamente en fallo.
    assert set(
        final["estado_fuentes"].values()
    ) == {
        "fallo"
    }

    assert final["evidencias"] == []


def test_consolidate_removes_duplicates_and_other_projects(adapters):
    """Verifica la limpieza de evidencias durante la consolidación."""

    adapters["github"].evidences += [
        # Misma fuente e ID: debe eliminarse como duplicado.
        ev(
            "github",
            "sha-1",
            "2026-10-10T15:00:00Z",
        ),

        # Evidencia de otro proyecto: debe descartarse.
        ev(
            "github",
            "sha-otro",
            "2026-10-10T15:00:00Z",
            99,
        ),

        # Evidencia de Notion devuelta por el adaptador GitHub:
        # no corresponde a la fuente y debe descartarse.
        ev(
            "notion",
            "tarea-intrusa",
            "2026-10-10T15:00:00Z",
        ),
    ]

    final = run(adapters)

    keys = [
        (e.fuente, e.id_externo)
        for e in final["evidencias"]
    ]

    # Deben quedar únicamente las tres evidencias válidas y únicas.
    assert len(keys) == len(set(keys)) == 3

    # Las evidencias inválidas no deben llegar al resultado final.
    assert ("github", "sha-otro") not in keys
    assert ("notion", "tarea-intrusa") not in keys


def test_invalid_cutoff_stops_before_calling_sources(adapters):
    """Verifica que una fecha inválida detenga el flujo antes de consultar fuentes."""

    # La fecha no incluye zona horaria, por lo que debe rechazarse.
    with pytest.raises(
        ValueError,
        match="zona horaria",
    ):
        run(
            adapters,
            cutoff="2026-10-12T23:59:59",
        )

    # Ningún adaptador debe haber sido consultado,
    # porque la validación ocurre antes de ejecutar los agentes.
    assert all(
        adapter.calls == []
        for adapter in adapters.values()
    )