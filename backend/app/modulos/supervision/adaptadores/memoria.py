"""AR-02: repositorio temporal de cortes en memoria."""

from copy import deepcopy
from datetime import datetime, timezone

from app.modulos.supervision.grafo.estado import EstadoSupervision


def _fecha_utc(valor: str) -> datetime:
    """Normaliza una fecha ISO 8601 con zona horaria."""
    fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))

    if fecha.tzinfo is None:
        raise ValueError("La fecha de corte debe incluir zona horaria.")

    return fecha.astimezone(timezone.utc)


class RepositorioSupervisionMemoria:
    """Guarda cortes mientras no se conecta PostgreSQL.

    Cada clave combina proyecto y fecha de corte normalizada.
    Guardar la misma clave reemplaza el corte anterior.
    Los datos se pierden al finalizar el proceso.
    """

    def __init__(self) -> None:
        self._cortes: dict[
            tuple[int, datetime], EstadoSupervision
        ] = {}

    def guardar(self, estado: EstadoSupervision) -> None:
        clave = (
            estado["proyecto_id"],
            _fecha_utc(estado["fecha_corte"]),
        )
        self._cortes[clave] = deepcopy(estado)

    def obtener(
        self,
        proyecto_id: int,
        fecha_corte: str,
    ) -> EstadoSupervision | None:
        clave = (proyecto_id, _fecha_utc(fecha_corte))
        estado = self._cortes.get(clave)

        if estado is None:
            return None

        return deepcopy(estado)

    def listar(
        self,
        proyecto_id: int,
    ) -> list[EstadoSupervision]:
        cortes = [
            (fecha, estado)
            for (proyecto, fecha), estado in self._cortes.items()
            if proyecto == proyecto_id
        ]
        cortes.sort(key=lambda corte: corte[0])

        return [deepcopy(estado) for _, estado in cortes]