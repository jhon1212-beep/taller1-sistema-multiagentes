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


def _response_text(response: Any) -> str:
    """Extrae el texto de una respuesta de Gemini o un objeto simulado."""
    text = getattr(response, "text", None)
    if callable(text):
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

        return ChatGoogleGenerativeAI(
            model=model or os.environ["GEMINI_MODEL"],
            google_api_key=api_key or os.environ["GEMINI_API_KEY"],
            temperature=0,
            max_retries=0,
            timeout=30,
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
