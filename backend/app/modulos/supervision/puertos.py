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
    ) -> Mapping[str, int] | None:
        """Guarda un corte. El repositorio SQL devuelve cuántas filas guardó."""
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


class RepositorioCortes(RepositorioSupervision, Protocol):
    """TA-018/TA-022: consultas por corte que necesita la API de supervisión.

    Amplía RepositorioSupervision sin cambiarlo; lo implementa
    SqlSupervisionRepository. Los días se reciben como «AAAA-MM-DD».
    """

    def obtener_ultimo(self, proyecto_id: int) -> EstadoSupervision | None:
        ...

    def obtener_indicadores(
        self,
        proyecto_id: int,
        fecha_corte: str | None = None,
    ) -> dict[str, Any] | None:
        ...

    def history(self, project_id: int) -> list[dict[str, Any]]:
        ...
