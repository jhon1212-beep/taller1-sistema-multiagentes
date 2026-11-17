"""TA-023: usa una plantilla cuando el generador principal falla."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.modulos.supervision.dominio import Alerta, Explicacion
from app.modulos.supervision.explicacion import explicar_en_lote
from app.modulos.supervision.puertos import GeneradorExplicacion

RATE_LIMIT = "rate_limit"
UNAVAILABLE = "error"


def classify_error(error: Exception) -> str:
    """Clasifica los errores de límite de cuota frente a otros fallos."""
    code = getattr(error, "status_code", None) or getattr(error, "code", None)
    text = f"{type(error).__name__} {error}".lower()
    if code == 429 or "429" in text or "resource_exhausted" in text or "ratelimit" in text:
        return RATE_LIMIT
    return UNAVAILABLE


class ResilientExplanationGenerator:
    """Intenta con Gemini y utiliza la plantilla si hay una excepción."""

    def __init__(
        self, primary: GeneradorExplicacion, fallback: GeneradorExplicacion
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self.fallbacks: list[dict[str, str]] = []

    def generar(
        self,
        alerta: Alerta,
        fecha_corte: str,
        contexto: Sequence[Mapping[str, Any]] | None = None,
    ) -> Explicacion:
        """Conserva la alerta y registra únicamente el tipo de fallo."""
        try:
            return self._primary.generar(alerta, fecha_corte, contexto=contexto)
        except Exception as error:  # Cualquier fallo del LLM activa el respaldo.
            self.fallbacks.append({
                "regla": alerta["regla"],
                "motivo": classify_error(error),
                "detalle": type(error).__name__,
            })
            return self._fallback.generar(alerta, fecha_corte, contexto=contexto)

    def generar_lote(
        self,
        alertas: Sequence[Alerta],
        fecha_corte: str,
        contextos: Sequence[Sequence[Mapping[str, Any]]] | None = None,
    ) -> list[Explicacion]:
        """TA-046: una solicitud por corte; si falla, la plantilla explica todas."""
        if not alertas:
            return []
        try:
            return explicar_en_lote(self._primary, alertas, fecha_corte, contextos)
        except Exception as error:  # 429, JSON inválido, número de textos distinto…
            motivo, detalle = classify_error(error), type(error).__name__
            self.fallbacks.extend(
                {"regla": a["regla"], "motivo": motivo, "detalle": detalle} for a in alertas
            )
            return explicar_en_lote(self._fallback, alertas, fecha_corte, contextos)

