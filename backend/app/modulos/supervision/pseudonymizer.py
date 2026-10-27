"""TA-023: seudonimiza evidencias antes de enviarlas a Gemini.

Los nombres de autores se sustituyen por alias estables durante la ejecución.
La verificación obligatoria revisa también el prompt final.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

ALIAS_PREFIX = "Member"
NO_AUTHOR = "Unassigned"
GENERIC_NAME = "[member]"
MAX_DESCRIPTION = 200
SAFE_FIELDS = ("fuente", "id_externo", "fecha", "estado", "fecha_limite", "tipo_archivo")


def _field(evidence: Any, name: str) -> Any:
    """Lee un atributo tanto de una instancia como de un diccionario."""
    if isinstance(evidence, Mapping):
        return evidence.get(name)
    return getattr(evidence, name, None)


class Pseudonymizer:
    """Asigna alias y sustituye nombres completos o fragmentos reconocidos."""

    def __init__(self, names: Iterable[str | None]) -> None:
        self._aliases: dict[str, str] = {}
        for name in names:
            key = (name or "").strip().casefold()
            if key and key not in self._aliases:
                self._aliases[key] = f"{ALIAS_PREFIX} {len(self._aliases) + 1}"

        # Si un fragmento de nombre es compartido, usamos un marcador neutro.
        token_owner: dict[str, str] = {}
        for full, alias in self._aliases.items():
            for token in full.split():
                if len(token) < 3:
                    continue
                if token not in token_owner:
                    token_owner[token] = alias
                elif token_owner[token] != alias:
                    token_owner[token] = GENERIC_NAME

        replacements = dict(self._aliases)
        for token, alias in token_owner.items():
            replacements.setdefault(token, alias)

        # Los nombres completos van primero para evitar sustituciones parciales.
        self._patterns = [
            (re.compile(rf"(?<!\w){re.escape(text)}(?!\w)", re.IGNORECASE), alias)
            for text, alias in sorted(replacements.items(), key=lambda item: -len(item[0]))
        ]

    @classmethod
    def from_evidences(cls, evidences: Iterable[Any]) -> "Pseudonymizer":
        """Construye un seudonimizador a partir de los autores conocidos."""
        return cls(_field(evidence, "autor") for evidence in evidences)

    def alias(self, name: str | None) -> str:
        """Devuelve un alias; nunca devuelve el nombre real."""
        key = (name or "").strip().casefold()
        if not key:
            return NO_AUTHOR
        return self._aliases.get(key, GENERIC_NAME)

    def scrub(self, text: str | None) -> str:
        """Elimina los nombres conocidos y limita el tamaño del texto."""
        cleaned = text or ""
        for pattern, alias in self._patterns:
            cleaned = pattern.sub(alias, cleaned)
        return cleaned[:MAX_DESCRIPTION]

    def evidence_context(self, evidence: Any) -> dict[str, Any]:
        """Prepara campos permitidos para el prompt de Gemini."""
        context = {
            name: _field(evidence, name)
            for name in SAFE_FIELDS
            if _field(evidence, name) is not None
        }
        context["autor"] = self.alias(_field(evidence, "autor"))
        context["descripcion"] = self.scrub(_field(evidence, "descripcion"))
        return context

    def alert_context(
        self, alert: Mapping[str, Any], evidences: Iterable[Any]
    ) -> list[dict[str, Any]]:
        """Incluye únicamente las evidencias relacionadas con la alerta."""
        wanted = set(alert.get("evidencia_ids") or [])
        return [
            self.evidence_context(evidence)
            for evidence in evidences
            if _field(evidence, "fuente") == alert.get("fuente")
            and str(_field(evidence, "id_externo")) in wanted
        ]
