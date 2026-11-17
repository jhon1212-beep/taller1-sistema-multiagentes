"""TA-023: generador de explicaciones con Gemini y control de cuota."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Mapping, Sequence

from app.modulos.supervision.adaptadores.plantilla import DESCRIPCIONES
from app.modulos.supervision.dominio import Alerta, Explicacion

DEFAULT_MIN_INTERVAL_SECONDS = 13.0

PROMPT_TEMPLATE = """You support a teacher reviewing student software projects.
Write 2 or 3 neutral sentences in Spanish explaining why the alert was raised
and what should be checked. Use ONLY the provided facts. Do not invent names
or numbers. Refer to people only by the pseudonyms in the evidence.

Rule: {rule} - {description}
Source: {source}
Cutoff: {cutoff}
Pseudonymized evidence:
{evidence}
"""


def build_explanation_prompt(
    alerta: Alerta,
    fecha_corte: str,
    contexto: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Construye el prompt usando únicamente el contexto seudonimizado."""
    evidence = (
        json.dumps(list(contexto), ensure_ascii=False, indent=2)
        if contexto
        else json.dumps({"evidencia_ids": alerta["evidencia_ids"]}, ensure_ascii=False)
    )
    return PROMPT_TEMPLATE.format(
        rule=alerta["regla"],
        description=DESCRIPCIONES.get(alerta["regla"], ""),
        source=alerta["fuente"],
        cutoff=fecha_corte,
        evidence=evidence,
    )


BATCH_PROMPT_TEMPLATE = """You support a teacher reviewing student software projects.
For EACH alert below, write 2 or 3 neutral sentences in Spanish explaining why it
was raised and what should be checked. Use ONLY the facts given for that alert.
Do not invent names or numbers. Refer to people only by their pseudonyms.

When an alert has a "reason", it was computed by deterministic rules: restate it
faithfully, do not claim the student lied, and suggest that the teacher open the
commit to check it.

Answer with a JSON array of exactly {count} strings and nothing else: the string
at position i explains the alert whose "index" is i, in the same order.

Cutoff: {cutoff}
Alerts:
{alerts}
"""


def build_batch_prompt(
    alertas: Sequence[Alerta],
    fecha_corte: str,
    contextos: Sequence[Sequence[Mapping[str, Any]]] | None = None,
) -> str:
    """TA-046: un solo prompt con todas las alertas del corte, ya seudonimizadas."""
    items = []
    for index, alerta in enumerate(alertas):
        contexto = contextos[index] if contextos else None
        items.append({
            "index": index,
            "rule": alerta["regla"],
            "description": DESCRIPCIONES.get(alerta["regla"], ""),
            "source": alerta["fuente"],
            "evidence": list(contexto) if contexto else {"evidencia_ids": alerta["evidencia_ids"]},
            **({"reason": alerta["motivo"]} if alerta.get("motivo") else {}),
        })
    return BATCH_PROMPT_TEMPLATE.format(
        count=len(alertas),
        cutoff=fecha_corte,
        alerts=json.dumps(items, ensure_ascii=False, indent=2),
    )


def parse_batch_answer(text: str, expected: int) -> list[str]:
    """Lee el arreglo JSON de la respuesta; cualquier forma inesperada es un error.

    Gemini a veces envuelve el JSON en ```json ... ```; se retira ese marco.
    Un número de textos distinto al de alertas, o un texto vacío, se rechaza
    para que el respaldo use la plantilla en vez de asignar mal una explicación.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned[cleaned.find("["):] if "[" in cleaned else cleaned
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("Gemini did not return a JSON array.")
    data = json.loads(cleaned[start:end + 1])
    if not isinstance(data, list) or len(data) != expected:
        raise ValueError(f"Gemini returned {len(data) if isinstance(data, list) else 0} texts for {expected} alerts.")
    texts = [str(item).strip() for item in data]
    if not all(texts):
        raise ValueError("Gemini returned an empty explanation.")
    return texts


def _response_text(response: Any) -> str:
    """Extrae el texto de una respuesta de Gemini o un objeto simulado."""
    text = getattr(response, "text", None)
    if not isinstance(text, str) and callable(text):
        text = text()
    if not isinstance(text, str):
        content = getattr(response, "content", response)
        text = content if isinstance(content, str) else str(content)
    return text.strip()


class GeminiExplanationGenerator:
    """Redacta una alerta previamente detectada por un motor determinista."""

    def __init__(
        self,
        llm: Any | None = None,
        *,
        model: str | None = None,
        api_key: str | None = None,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        # Inyección del LLM: las pruebas no necesitan claves ni conexión.
        # Creación diferida: permite respaldar errores de configuración de Gemini.
        self._llm = llm
        self._model = model
        self._api_key = api_key
        self._min_interval = min_interval_seconds
        self._sleep = sleep
        self._clock = clock
        self._last_call: float | None = None

    @staticmethod
    def _create_llm(model: str | None, api_key: str | None) -> Any:
        """Crea el cliente real solo cuando es necesario."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        # TA-046: razonamiento reducido. GEMINI_THINKING_BUDGET (tokens, 0 = sin
        # razonamiento) o GEMINI_REASONING_EFFORT (low | medium | high) se pasan
        # solo si están definidas, porque no todos los modelos aceptan ambas.
        extra: dict[str, Any] = {}
        if os.getenv("GEMINI_THINKING_BUDGET", "").strip():
            extra["thinking_budget"] = int(os.environ["GEMINI_THINKING_BUDGET"])
        if os.getenv("GEMINI_REASONING_EFFORT", "").strip():
            extra["reasoning_effort"] = os.environ["GEMINI_REASONING_EFFORT"].strip()
        return ChatGoogleGenerativeAI(
            model=model or os.environ["GEMINI_MODEL"],
            google_api_key=api_key or os.environ["GEMINI_API_KEY"],
            temperature=0,
            max_retries=0,
            timeout=60,
            **extra,
        )

    def _throttle(self) -> None:
        """Respeta el intervalo configurado entre solicitudes."""
        if self._last_call is not None:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def generar(
        self,
        alerta: Alerta,
        fecha_corte: str,
        contexto: Sequence[Mapping[str, Any]] | None = None,
    ) -> Explicacion:
        """Solicita solo la explicación; no calcula ni modifica la regla."""
        self._throttle()
        prompt = build_explanation_prompt(alerta, fecha_corte, contexto)
        if self._llm is None:
            self._llm = self._create_llm(self._model, self._api_key)
        text = _response_text(self._llm.invoke(prompt))
        if not text:
            raise ValueError("Gemini returned an empty response.")
        return {"texto": text, "origen": "gemini"}

    def generar_lote(
        self,
        alertas: Sequence[Alerta],
        fecha_corte: str,
        contextos: Sequence[Sequence[Mapping[str, Any]]] | None = None,
    ) -> list[Explicacion]:
        """TA-046: una sola solicitud a Gemini por proyecto y corte."""
        if not alertas:
            return []
        self._throttle()
        prompt = build_batch_prompt(alertas, fecha_corte, contextos)
        if self._llm is None:
            self._llm = self._create_llm(self._model, self._api_key)
        texts = parse_batch_answer(_response_text(self._llm.invoke(prompt)), len(alertas))
        return [{"texto": text, "origen": "gemini"} for text in texts]
