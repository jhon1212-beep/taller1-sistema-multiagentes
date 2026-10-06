"""AR-02: pruebas del contrato de supervision."""

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.supervision.adaptadores.memoria import (
    RepositorioSupervisionMemoria,
)
from app.modulos.supervision.adaptadores.plantilla import (
    GeneradorExplicacionPlantilla,
)
from app.modulos.supervision.grafo.estado import crear_estado_inicial


CORTE = "2026-10-06T00:00:00Z"


def crear_alerta(regla="R1", fuente="notion"):
    return {
        "regla": regla,
        "fuente": fuente,
        "evidencia_ids": ["evidencia-demo-1"],
        "explicacion": None,
        "origen_explicacion": None,
    }


def test_estados_iniciales_no_comparten_datos_mutables():
    primero = crear_estado_inicial(1, CORTE)
    segundo = crear_estado_inicial(2, CORTE)

    primero["evidencias"].append(
        Evidencia("github", "sha-demo", "autor-demo", CORTE, "Commit", 1)
    )
    primero["estado_fuentes"]["github"] = "ok"
    primero["indicadores"]["I1"] = 50.0
    primero["alertas"].append(crear_alerta())

    assert segundo["evidencias"] == []
    assert segundo["estado_fuentes"]["github"] == "pendiente"
    assert segundo["indicadores"]["I1"] is None
    assert segundo["alertas"] == []


def test_plantilla_explica_las_cuatro_reglas_con_referencias():
    generador = GeneradorExplicacionPlantilla()

    for regla, fuente in [
        ("R1", "notion"),
        ("R2", "notion"),
        ("R3", "github"),
        ("R4", "drive"),
    ]:
        resultado = generador.generar(crear_alerta(regla, fuente), CORTE)

        assert resultado["origen"] == "plantilla"
        assert f"Regla {regla}:" in resultado["texto"]
        assert f"Fuente: {fuente}" in resultado["texto"]
        assert CORTE in resultado["texto"]
        assert "evidencia-demo-1" in resultado["texto"]


def test_plantilla_rechaza_regla_o_fuente_incorrectas():
    generador = GeneradorExplicacionPlantilla()

    with pytest.raises(ValueError, match="desconocida"):
        generador.generar(crear_alerta("R5", "notion"), CORTE)

    with pytest.raises(ValueError, match="fuente"):
        generador.generar(crear_alerta("R1", "github"), CORTE)


def test_repositorio_aisla_el_estado_guardado_y_el_consultado():
    repositorio = RepositorioSupervisionMemoria()
    original = crear_estado_inicial(1, CORTE)
    original["evidencias"].append(
        Evidencia("github", "sha-demo", "autor-demo", CORTE, "Commit", 1)
    )
    repositorio.guardar(original)

    original["evidencias"][0].descripcion = "Cambio externo"

    consultado = repositorio.obtener(1, CORTE)
    assert consultado is not None
    assert consultado["evidencias"][0].descripcion == "Commit"

    consultado["evidencias"][0].descripcion = "Cambio en consulta"

    nuevamente = repositorio.obtener(1, CORTE)
    assert nuevamente is not None
    assert nuevamente["evidencias"][0].descripcion == "Commit"


def test_repositorio_reemplaza_fechas_equivalentes_y_separa_proyectos():
    repositorio = RepositorioSupervisionMemoria()
    repositorio.guardar(crear_estado_inicial(1, CORTE))

    reemplazo = crear_estado_inicial(1, "2026-10-05T19:00:00-05:00")
    reemplazo["indicadores"]["I1"] = 75.0
    repositorio.guardar(reemplazo)
    repositorio.guardar(crear_estado_inicial(2, CORTE))

    assert len(repositorio.listar(1)) == 1
    resultado = repositorio.obtener(1, CORTE)
    assert resultado is not None
    assert resultado["indicadores"]["I1"] == 75.0
    assert len(repositorio.listar(2)) == 1
    assert repositorio.obtener(3, CORTE) is None


def test_historial_ordenado_independiente_y_fecha_con_zona_obligatoria():
    repositorio = RepositorioSupervisionMemoria()
    repositorio.guardar(crear_estado_inicial(1, CORTE))
    repositorio.guardar(
        crear_estado_inicial(1, "2026-10-05T00:00:00Z")
    )

    historial = repositorio.listar(1)
    assert [corte["fecha_corte"] for corte in historial] == [
        "2026-10-05T00:00:00Z",
        CORTE,
    ]

    historial[0]["indicadores"]["I1"] = 99.0
    assert repositorio.listar(1)[0]["indicadores"]["I1"] is None
    assert repositorio.listar(3) == []

    with pytest.raises(ValueError, match="zona horaria"):
        repositorio.guardar(
            crear_estado_inicial(1, "2026-10-06T00:00:00")
        )