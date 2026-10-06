"""TA-012: pruebas locales del grafo de supervision."""

import pytest
from langsmith import tracing_context

from app.modulos.evidencias.adaptadores.falso import (
    FuenteEvidenciaFalsa,
)
from app.modulos.supervision.grafo.construir_grafo import (
    construir_grafo,
)
from app.modulos.supervision.grafo.estado import (
    crear_estado_inicial,
)


REFERENCIAS = {
    "github": "repositorio-demo",
    "notion": "base-demo",
    "drive": "carpeta-demo",
}
FECHA_CORTE = "2026-10-06T00:00:00Z"


@pytest.fixture(autouse=True)
def desactivar_trazas():
    """Las pruebas funcionan sin enviar trazas a LangSmith."""
    with tracing_context(enabled=False):
        yield


def test_grafo_consolida_las_tres_fuentes_sin_duplicados():
    grafo = construir_grafo(
        FuenteEvidenciaFalsa(),
        REFERENCIAS,
    )
    inicial = crear_estado_inicial(1, FECHA_CORTE)

    resultado = grafo.invoke(inicial)

    assert len(resultado["evidencias"]) == 3
    assert {
        evidencia.fuente
        for evidencia in resultado["evidencias"]
    } == {"github", "notion", "drive"}

    claves = [
        (evidencia.fuente, evidencia.id_externo)
        for evidencia in resultado["evidencias"]
    ]
    assert len(claves) == len(set(claves))
    assert all(
        evidencia.proyecto_id == 1
        for evidencia in resultado["evidencias"]
    )
    assert resultado["estado_fuentes"] == {
        "github": "ok",
        "notion": "ok",
        "drive": "ok",
    }
    assert all(
        error is None
        for error in resultado["errores_fuentes"].values()
    )
    assert resultado["indicadores"] == inicial["indicadores"]
    assert resultado["alertas"] == []


def test_grafo_consulta_cada_referencia_con_el_proyecto():
    class FuenteRegistradora(FuenteEvidenciaFalsa):
        def __init__(self):
            self.llamadas = []

        def obtener_evidencias(
            self,
            referencia,
            proyecto_id,
            *,
            limite=None,
            desde=None,
        ):
            self.llamadas.append((referencia, proyecto_id))
            return super().obtener_evidencias(
                referencia,
                proyecto_id,
                limite=limite,
                desde=desde,
            )

    fuente = FuenteRegistradora()
    grafo = construir_grafo(fuente, REFERENCIAS)

    grafo.invoke(crear_estado_inicial(1, FECHA_CORTE))

    assert fuente.llamadas == [
        ("repositorio-demo", 1),
        ("base-demo", 1),
        ("carpeta-demo", 1),
    ]


def test_grafo_no_mezcla_evidencias_de_otro_proyecto():
    grafo = construir_grafo(
        FuenteEvidenciaFalsa(),
        REFERENCIAS,
    )

    resultado = grafo.invoke(
        crear_estado_inicial(999, FECHA_CORTE)
    )

    assert resultado["proyecto_id"] == 999
    assert resultado["evidencias"] == []
    assert all(
        estado == "ok"
        for estado in resultado["estado_fuentes"].values()
    )
    assert all(
        error is None
        for error in resultado["errores_fuentes"].values()
    )


def test_grafo_continua_si_una_fuente_falla():
    class FuenteConFallo(FuenteEvidenciaFalsa):
        def obtener_evidencias(
            self,
            referencia,
            proyecto_id,
            *,
            limite=None,
            desde=None,
        ):
            if referencia == REFERENCIAS["notion"]:
                raise RuntimeError("Notion no disponible")

            return super().obtener_evidencias(
                referencia,
                proyecto_id,
                limite=limite,
                desde=desde,
            )

    grafo = construir_grafo(
        FuenteConFallo(),
        REFERENCIAS,
    )

    resultado = grafo.invoke(
        crear_estado_inicial(1, FECHA_CORTE)
    )

    assert resultado["estado_fuentes"] == {
        "github": "ok",
        "notion": "fallo",
        "drive": "ok",
    }
    assert resultado["errores_fuentes"]["notion"] == (
        "RuntimeError: Notion no disponible"
    )
    assert resultado["errores_fuentes"]["github"] is None
    assert resultado["errores_fuentes"]["drive"] is None
    assert {
        evidencia.fuente
        for evidencia in resultado["evidencias"]
    } == {"github", "drive"}


def test_grafo_rechaza_referencias_incompletas():
    referencias = {
        "github": "repositorio-demo",
        "notion": "base-demo",
    }

    with pytest.raises(ValueError, match="drive"):
        construir_grafo(
            FuenteEvidenciaFalsa(),
            referencias,
        )