"""TA-046: una solicitud a Gemini por proyecto y corte, con todas sus alertas.

Criterios: 1) 1 llamada por proyecto y corte; 2) razonamiento reducido
(configurable); 3) los escenarios de TA-023 siguen en verde (ver
test_explainable_alerts.py). Gemini se simula: no se gasta cuota.
"""
import json
import re

import pytest

from app.modulos.supervision.adaptadores.gemini import (
    GeminiExplanationGenerator,
    build_batch_prompt,
    parse_batch_answer,
)
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.adaptadores.resilient import (
    RATE_LIMIT,
    ResilientExplanationGenerator,
)
from app.modulos.supervision.explicacion import explicar_en_lote

CUTOFF = "2026-10-12T23:59:59-05:00"
ALERTS = [
    {"regla": "R1", "fuente": "notion", "evidencia_ids": ["t1"], "explicacion": None, "origen_explicacion": None},
    {"regla": "R2", "fuente": "notion", "evidencia_ids": ["t2"], "explicacion": None, "origen_explicacion": None},
    {"regla": "R3", "fuente": "github", "evidencia_ids": ["c1"], "explicacion": None, "origen_explicacion": None},
]
CONTEXTS = [[{"id": "t1", "autor": "Member 1"}], [{"id": "t2", "autor": "Member 2"}], [{"id": "c1", "autor": "Member 1"}]]


class FakeLLM:
    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.prompts = answer, error, []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        if self.answer is not None:
            return type("R", (), {"text": self.answer})()
        n = int(re.search(r"exactly (\d+) strings", prompt).group(1))
        return type("R", (), {"text": json.dumps([f"Texto {i}" for i in range(n)])})()


class RateLimitError(Exception):
    status_code = 429


def gemini(llm):
    return GeminiExplanationGenerator(llm, min_interval_seconds=0)


def test_una_sola_llamada_para_todas_las_alertas_y_en_orden():
    llm = FakeLLM()
    result = gemini(llm).generar_lote(ALERTS, CUTOFF, CONTEXTS)
    assert len(llm.prompts) == 1
    assert [r["texto"] for r in result] == ["Texto 0", "Texto 1", "Texto 2"]
    assert {r["origen"] for r in result} == {"gemini"}


def test_el_prompt_lleva_cada_alerta_con_su_indice_y_solo_seudonimos():
    prompt = build_batch_prompt(ALERTS, CUTOFF, CONTEXTS)
    assert "exactly 3 strings" in prompt
    assert '"index": 2' in prompt and '"rule": "R3"' in prompt
    assert "Member 1" in prompt


def test_sin_alertas_no_se_llama_a_gemini():
    llm = FakeLLM()
    assert gemini(llm).generar_lote([], CUTOFF) == []
    assert llm.prompts == []


@pytest.mark.parametrize("answer", [
    "```json\n[\"a\", \"b\", \"c\"]\n```",
    'Aquí van: ["a", "b", "c"]',
])
def test_acepta_el_arreglo_aunque_venga_envuelto(answer):
    assert parse_batch_answer(answer, 3) == ["a", "b", "c"]


@pytest.mark.parametrize("answer", ['["a", "b"]', '["a", "", "c"]', "sin json", '{"a": 1}'])
def test_rechaza_respuestas_que_no_calzan_con_las_alertas(answer):
    with pytest.raises(ValueError):
        parse_batch_answer(answer, 3)


def test_429_usa_la_plantilla_para_todas_y_registra_cada_respaldo():
    resilient = ResilientExplanationGenerator(
        gemini(FakeLLM(error=RateLimitError("429"))), GeneradorExplicacionPlantilla()
    )
    result = resilient.generar_lote(ALERTS, CUTOFF, CONTEXTS)
    assert {r["origen"] for r in result} == {"plantilla"}
    assert [f["regla"] for f in resilient.fallbacks] == ["R1", "R2", "R3"]
    assert {f["motivo"] for f in resilient.fallbacks} == {RATE_LIMIT}


def test_respuesta_incompleta_no_asigna_mal_las_explicaciones():
    resilient = ResilientExplanationGenerator(
        gemini(FakeLLM(answer='["solo una"]')), GeneradorExplicacionPlantilla()
    )
    result = resilient.generar_lote(ALERTS, CUTOFF, CONTEXTS)
    assert {r["origen"] for r in result} == {"plantilla"}
    assert len(resilient.fallbacks) == 3


def test_un_generador_sin_lote_se_usa_alerta_por_alerta():
    class SoloUno:
        def __init__(self):
            self.llamadas = 0

        def generar(self, alerta, fecha_corte, contexto=None):
            self.llamadas += 1
            return {"texto": alerta["regla"], "origen": "plantilla"}

    generador = SoloUno()
    assert [e["texto"] for e in explicar_en_lote(generador, ALERTS, CUTOFF)] == ["R1", "R2", "R3"]
    assert generador.llamadas == 3


def test_razonamiento_reducido_se_configura_por_variable(monkeypatch):
    capturado = {}

    class FalsoChat:
        def __init__(self, **kwargs):
            capturado.update(kwargs)

    import langchain_google_genai
    monkeypatch.setattr(langchain_google_genai, "ChatGoogleGenerativeAI", FalsoChat)
    monkeypatch.setenv("GEMINI_THINKING_BUDGET", "0")
    monkeypatch.delenv("GEMINI_REASONING_EFFORT", raising=False)
    GeminiExplanationGenerator._create_llm("gemini-modelo", "clave")
    assert capturado["thinking_budget"] == 0 and capturado["temperature"] == 0

    capturado.clear()
    monkeypatch.delenv("GEMINI_THINKING_BUDGET")
    GeminiExplanationGenerator._create_llm("gemini-modelo", "clave")
    assert "thinking_budget" not in capturado
