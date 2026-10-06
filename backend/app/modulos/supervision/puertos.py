"""AR-02: contratos del modulo supervision."""

from __future__ import annotations

from typing import Protocol

from app.modulos.supervision.dominio import Alerta, Explicacion
from app.modulos.supervision.grafo.estado import EstadoSupervision


class GeneradorExplicacion(Protocol):
    """Contrato para Gemini o la plantilla de respaldo."""

    def generar(
        self,
        alerta: Alerta,
        fecha_corte: str,
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