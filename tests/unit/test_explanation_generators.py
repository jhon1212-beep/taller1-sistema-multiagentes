"""TA-023: comprueba Gemini, límites de llamadas y respaldo CP-19."""
import pytest

from app.modulos.supervision.adaptadores.gemini import GeminiExplanationGenerator, build_explanation_prompt
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.adaptadores.resilient import (
    RATE_LIMIT, UNAVAILABLE, ResilientExplanationGenerator, classify_error,
)

CUTOFF = "2026-10-12T23:59:59-05:00"
ALERT = {"regla": "R2", "fuente": "notion", "evidencia_ids": ["t1"],
         "explicacion": None, "origen_explicacion": None}
CONTEXT = [{"fuente": "notion", "id_externo": "t1", "estado": "En curso",
            "autor": "Member 1", "descripcion": "Catalog module"}]


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeLLM:
    """Responde sin conectar con Gemini y registra los prompts."""
    def __init__(self, answer="The task has had no updates for over 7 days.", error=None):
        self.answer = answer
        self.error = error
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return FakeResponse(self.answer)


class RateLimitError(Exception):
    status_code = 429


def gemini(llm):
    return GeminiExplanationGenerator(llm, min_interval_seconds=0)


def test_prompt_includes_rule_cutoff_and_pseudonymized_evidence():
    prompt = build_explanation_prompt(ALERT, CUTOFF, CONTEXT)
    assert "R2" in prompt and CUTOFF in prompt
    assert "Member 1" in prompt and "Catalog module" in prompt


def test_gemini_returns_text_marked_as_gemini():
    llm = FakeLLM()
    result = gemini(llm).generar(ALERT, CUTOFF, contexto=CONTEXT)
    assert result == {"texto": "The task has had no updates for over 7 days.", "origen": "gemini"}
    assert len(llm.prompts) == 1


def test_gemini_rejects_an_empty_answer():
    with pytest.raises(ValueError):
        gemini(FakeLLM(answer=" ")).generar(ALERT, CUTOFF)


def test_gemini_waits_between_calls_to_respect_5_rpm():
    waits = []
    clock = iter([0.0, 2.0, 15.0])
    generator = GeminiExplanationGenerator(
        FakeLLM(), min_interval_seconds=13,
        sleep=waits.append, clock=lambda: next(clock),
    )
    generator.generar(ALERT, CUTOFF)
    generator.generar(ALERT, CUTOFF)
    assert waits == [11.0]


@pytest.mark.parametrize(("error", "expected"), [
    (RateLimitError("quota"), RATE_LIMIT),
    (RuntimeError("429 RESOURCE_EXHAUSTED"), RATE_LIMIT),
    (TimeoutError("no response"), UNAVAILABLE),
])
def test_classify_error(error, expected):
    assert classify_error(error) == expected


def test_cp19_rate_limit_uses_template_and_marks_the_alert():
    resilient = ResilientExplanationGenerator(
        gemini(FakeLLM(error=RateLimitError("429"))),
        GeneradorExplicacionPlantilla(),
    )
    result = resilient.generar(ALERT, CUTOFF, contexto=CONTEXT)
    assert result["origen"] == "plantilla"
    assert result["texto"].startswith("Regla R2:")
    assert resilient.fallbacks[0]["regla"] == "R2"
    assert resilient.fallbacks[0]["motivo"] == RATE_LIMIT


def test_successful_gemini_does_not_record_a_fallback():
    resilient = ResilientExplanationGenerator(
        gemini(FakeLLM()), GeneradorExplicacionPlantilla()
    )
    assert resilient.generar(ALERT, CUTOFF)["origen"] == "gemini"
    assert resilient.fallbacks == []
