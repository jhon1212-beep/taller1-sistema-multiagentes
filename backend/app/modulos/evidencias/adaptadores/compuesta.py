import logging

logger = logging.getLogger("evidencias")


class FuenteEvidenciaCompuesta:
    """Reparte cada consulta al adaptador real según la referencia."""

    def __init__(self, por_referencia: dict):
        self._por_referencia = dict(por_referencia)

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        adaptador = self._por_referencia.get(referencia)
        if adaptador is None:
            raise ValueError(f"Sin adaptador para la referencia: {referencia}")
        try:
            return adaptador.obtener_evidencias(
                referencia, proyecto_id, limite=limite, desde=desde
            )
        except Exception as error:
            logger.error(
                "fuente fallida | referencia=%s | proyecto=%s | %s: %s",
                referencia, proyecto_id, type(error).__name__, error,
            )
            raise