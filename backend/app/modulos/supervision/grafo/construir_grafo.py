"""TA-012: grafo de supervision con fuentes intercambiables."""

from __future__ import annotations

from collections.abc import Mapping

from langgraph.graph import END, START, StateGraph

from app.modulos.evidencias.puertos import FuenteEvidencia
from app.modulos.supervision.dominio import Fuente
from app.modulos.supervision.grafo.estado import EstadoSupervision


FUENTES: tuple[Fuente, ...] = ("github", "notion", "drive")


def construir_grafo(
    fuente: FuenteEvidencia,
    referencias: Mapping[Fuente, str],
):
    """Construye el grafo usando el puerto FuenteEvidencia."""

    referencias_locales = dict(referencias)
    faltantes = [
        nombre
        for nombre in FUENTES
        if not referencias_locales.get(nombre)
    ]
    if faltantes:
        raise ValueError(
            "Faltan referencias para: " + ", ".join(faltantes)
        )

    def crear_nodo(nombre: Fuente):
        def consultar(estado: EstadoSupervision) -> dict:
            # Sustituye solo las evidencias de esta fuente.
            evidencias = [
                evidencia
                for evidencia in estado["evidencias"]
                if evidencia.fuente != nombre
            ]
            estados = dict(estado["estado_fuentes"])
            errores = dict(estado["errores_fuentes"])

            try:
                obtenidas = fuente.obtener_evidencias(
                    referencia=referencias_locales[nombre],
                    proyecto_id=estado["proyecto_id"],
                )

                # La fuente falsa devuelve las tres fuentes juntas.
                seleccionadas = [
                    evidencia
                    for evidencia in obtenidas
                    if evidencia.fuente == nombre
                    and evidencia.proyecto_id == estado["proyecto_id"]
                ]

                evidencias.extend(seleccionadas)
                estados[nombre] = "ok"
                errores[nombre] = None

            except Exception as error:
                # Una fuente fallida permite continuar con las demas.
                estados[nombre] = "fallo"
                errores[nombre] = (
                    f"{type(error).__name__}: {error}"
                )

            return {
                "evidencias": evidencias,
                "estado_fuentes": estados,
                "errores_fuentes": errores,
            }

        return consultar

    def consolidar(estado: EstadoSupervision) -> dict:
        """Elimina duplicados por fuente e identificador externo."""

        unicas = {}
        for evidencia in estado["evidencias"]:
            if evidencia.proyecto_id == estado["proyecto_id"]:
                clave = (
                    evidencia.fuente,
                    evidencia.id_externo,
                )
                unicas[clave] = evidencia

        return {"evidencias": list(unicas.values())}

    grafo = StateGraph(EstadoSupervision)

    for nombre in FUENTES:
        grafo.add_node(
            f"fuente_{nombre}",
            crear_nodo(nombre),
        )

    grafo.add_node("consolidar", consolidar)

    grafo.add_edge(START, "fuente_github")
    grafo.add_edge("fuente_github", "fuente_notion")
    grafo.add_edge("fuente_notion", "fuente_drive")
    grafo.add_edge("fuente_drive", "consolidar")
    grafo.add_edge("consolidar", END)

    return grafo.compile()