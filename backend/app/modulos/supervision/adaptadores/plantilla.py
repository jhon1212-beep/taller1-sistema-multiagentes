"""AR-02: explicaciones deterministas sin llamadas a un LLM."""

from app.modulos.supervision.dominio import Alerta, Explicacion


DESCRIPCIONES = {
    "R1": "Tarea no completada con fecha limite anterior al corte.",
    "R2": "Tarea en curso sin ediciones durante mas de 7 dias.",
    "R3": "Repositorio sin commits en los 7 dias previos al corte.",
    "R4": "Carpeta sin documentos modificados en los 14 dias previos al corte.",
}

FUENTES_POR_REGLA = {
    "R1": "notion",
    "R2": "notion",
    "R3": "github",
    "R4": "drive",
}


class GeneradorExplicacionPlantilla:
    """Explica una alerta que el motor ya ha detectado."""

    def generar(
        self,
        alerta: Alerta,
        fecha_corte: str,
    ) -> Explicacion:
        regla = alerta["regla"]

        if regla not in DESCRIPCIONES:
            raise ValueError(f"Regla de alerta desconocida: {regla}")

        if alerta["fuente"] != FUENTES_POR_REGLA[regla]:
            raise ValueError("La fuente no corresponde a la regla.")

        referencias = ", ".join(alerta["evidencia_ids"])
        if not referencias:
            referencias = "sin referencias disponibles"

        texto = (
            f"Regla {regla}: {DESCRIPCIONES[regla]} "
            f"Fuente: {alerta['fuente']}. "
            f"Fecha de corte: {fecha_corte}. "
            f"Referencias de evidencia: {referencias}."
        )

        return {
            "texto": texto,
            "origen": "plantilla",
        }