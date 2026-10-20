# -*- coding: utf-8 -*-
"""TA-010 · Esquema común de evidencia (Pydantic)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenciaNormalizada(BaseModel):
    """Los 6 campos comunes. Ninguno puede venir vacío."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    fuente: Literal["github", "notion", "drive"]
    id_externo: str = Field(min_length=1, max_length=255)
    autor: str = Field(min_length=1, max_length=255)
    fecha: datetime
    descripcion: str = Field(min_length=1)
    proyecto_id: int = Field(gt=0)

    @field_validator("fecha")
    @classmethod
    def _fecha_con_zona(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None:
            raise ValueError("La fecha debe incluir zona horaria.")
        return valor