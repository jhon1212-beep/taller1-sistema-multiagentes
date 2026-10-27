"""AR-02: contratos del modulo supervision."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from app.modulos.supervision.dominio import Alerta, Explicacion
from app.modulos.supervision.grafo.estado import EstadoSupervision


class GeneradorExplicacion(Protocol):
    """Contrato para Gemini o la plantilla de respaldo."""

    def generar(
        self,
        alerta: Alerta,
        fecha_corte: str,
        contexto: Sequence[Mapping[str, Any]] | None = None,
    ) -> Explicacion:
        ...


class RepositorioSupervision(Protocol):
    """Contrato para guardar y consultar cortes por proyecto."""

    def guardar(
        self,
        estado: EstadoSupervision,
    ) -> None:
        ...

    def obtener(
        self,
        proyecto_id: int,
        fecha_corte: str,
    ) -> EstadoSupervision | None:
        ...

    def listar(
        self,
        proyecto_id: int,
    ) -> list[EstadoSupervision]:
        ...