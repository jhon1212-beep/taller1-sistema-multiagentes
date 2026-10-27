"""TA-023: integra el Supervisor, motor, seudonimización y respaldo."""
import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langsmith")

from langsmith import tracing_context
from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.supervision.adaptadores.gemini import GeminiExplanationGenerator
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.adaptadores.resilient import RATE_LIMIT, ResilientExplanationGenerator
from app.modulos.supervision.grafo.supervisor import (
    EVALUATE_NODE, EXPLAIN_NODE, build_supervisor_graph,
    build_supervisor_input, to_consolidated_report,
)

CUTOFF = "2026-10-12T23:59:59-05:00"
REFERENCES = {"github": "repo-demo", "notion": "base-demo", "drive": "folder-demo"}
REAL_NAMES = ["Elena", "Ríos", "Carlos", "León"]


class FakeLLM:
    def __init__(self, error=None):
        self.error = error
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return type("Response", (), {"text": "Explanation produced by Gemini."})()


class RateLimitError(Exception):
    status_code = 429


@pytest.fixture(autouse=True)
def disable_tracing():
    with tracing_context(enabled=False):
        yield


def run(project_id=2, explainer=None, adapters=None):
    if adapters is None:
        adapters = {name: FuenteEvidenciaDataset(fuente=name) for name in REFERENCES}
    graph = build_supervisor_graph(adapters, explainer=explainer)
    return to_consolidated_report(
        graph.invoke(build_supervisor_input(project_id, CUTOFF, REFERENCES))
    )


def by_rule(report):
    rules = {}
    for alert in report["alertas"]:
        rules.setdefault(alert["regla"], []).append(alert)
    return rules


def test_graph_adds_evaluate_and_explain_after_consolidate():
    graph = build_supervisor_graph({name: FuenteEvidenciaDataset(fuente=name) for name in REFERENCES})
    assert {EVALUATE_NODE, EXPLAIN_NODE} <= set(graph.get_graph().nodes)


@pytest.mark.parametrize(("rule", "source", "expected_ids"), [
    ("R1", "notion", {"tarea-p2-04", "tarea-p2-07"}),
    ("R2", "notion", {"tarea-p2-04", "tarea-p2-05", "tarea-p2-06"}),
    ("R3", "github", {"31f68efa64c129a123afda04f2f1c97aa737cc46"}),
    ("R4", "drive", {"archivo-p2-06"}),
])
def test_cp12_to_cp15_one_alert_per_rule_with_its_evidence(rule, source, expected_ids):
    alerts = by_rule(run())[rule]
    assert {a["fuente"] for a in alerts} == {source}
    assert {i for a in alerts for i in a["evidencia_ids"]} == expected_ids
    assert len(alerts) == len(expected_ids)
    assert all(a["explicacion"] and a["origen_explicacion"] == "plantilla" for a in alerts)


def test_indicators_are_no_longer_none():
    assert run()["indicadores"] == {"I1": 37.5, "I2": 62.5, "I3": 2, "I4": 7}


def test_no_real_name_is_sent_to_gemini():
    llm = FakeLLM()
    report = run(explainer=GeminiExplanationGenerator(llm, min_interval_seconds=0))
    assert len(llm.prompts) == len(report["alertas"]) == 7
    sent = "\n".join(llm.prompts)
    assert not [name for name in REAL_NAMES if name in sent]
    assert "Member 1" in sent
    assert {a["origen_explicacion"] for a in report["alertas"]} == {"gemini"}


def test_cp19_gemini_429_falls_back_to_template_and_marks_every_alert():
    resilient = ResilientExplanationGenerator(
        GeminiExplanationGenerator(FakeLLM(error=RateLimitError("429")), min_interval_seconds=0),
        GeneradorExplicacionPlantilla(),
    )
    report = run(explainer=resilient)
    assert {a["origen_explicacion"] for a in report["alertas"]} == {"plantilla"}
    assert len(resilient.fallbacks) == 7
    assert {f["motivo"] for f in resilient.fallbacks} == {RATE_LIMIT}


def test_failed_source_does_not_trigger_inactivity_alerts():
    class Down:
        def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
            raise ConnectionError("GitHub is unavailable")

    adapters = {name: FuenteEvidenciaDataset(fuente=name) for name in REFERENCES}
    adapters["github"] = Down()
    report = run(adapters=adapters)
    assert report["fuentes"]["github"]["estado"] == "fallo"
    assert "R3" not in by_rule(report)
