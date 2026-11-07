"""HU-006 / HU-007: los datos de supervisión del frontend salen del motor de TA-019."""

import json
import re
from pathlib import Path

import pytest

import generar_demo_supervision as generador
from app.modulos.evidencias.dataset import cargar_dataset

RAIZ = Path(__file__).resolve().parents[2]
DEMO_JS = RAIZ / "frontend/src/datos/demo_supervision.js"


def _supervision_del_frontend() -> dict:
    texto = DEMO_JS.read_text(encoding="utf-8")
    cuerpo = re.search(r"export const SUPERVISION_DEMO = (\{.*\})\s*$", texto, re.S).group(1)
    return json.loads(cuerpo)


def test_el_archivo_del_frontend_esta_al_dia_con_el_generador():
    """Si cambia el motor o el dataset hay que volver a ejecutar generar_demo_supervision.py."""
    assert DEMO_JS.read_text(encoding="utf-8") == generador.a_js(generador.construir())


def test_las_alertas_del_frontend_son_las_esperadas_del_dataset():
    esperadas = cargar_dataset()["alertas_esperadas"]
    for pid, proyecto in _supervision_del_frontend().items():
        mostradas = {(a["regla"], a["evidencia_ids"][0]) for a in proyecto["alertas"]}
        assert mostradas == {(a["regla"], a["evidencia_id"]) for a in esperadas[pid]}


def test_el_proyecto_2_muestra_las_cuatro_reglas():
    reglas = {a["regla"] for a in _supervision_del_frontend()["2"]["alertas"]}
    assert reglas == {"R1", "R2", "R3", "R4"}


def test_toda_alerta_lleva_explicacion_y_evidencia():
    """RN-003: ninguna alerta se muestra sin su evidencia de origen."""
    for proyecto in _supervision_del_frontend().values():
        for alerta in proyecto["alertas"]:
            assert alerta["explicacion"].startswith(f"Regla {alerta['regla']}:")
            assert alerta["origen_explicacion"] == "plantilla"
            assert alerta["evidencia"]["id"] == alerta["evidencia_ids"][0]
            assert alerta["evidencia"]["titulo"]


def test_i1_i3_e_i4_coinciden_con_el_dataset():
    esperados = cargar_dataset()["indicadores_esperados"]
    for pid, proyecto in _supervision_del_frontend().items():
        for clave in ("I1", "I3", "I4"):
            assert proyecto["indicadores"][clave] == esperados[pid][clave]


def test_i2_del_frontend_es_el_porcentaje_de_tareas_no_completadas():
    """La definición que usa el Supervisor (motor_indicadores): I2 = 100 − I1."""
    for proyecto in _supervision_del_frontend().values():
        ind = proyecto["indicadores"]
        assert ind["I2"] == pytest.approx(100 - ind["I1"])


@pytest.mark.xfail(
    reason="Inconsistencia conocida: motor.py (TA-019, dataset y docs) define I2 como «Sin empezar»; "
    "motor_indicadores.py, que usa el Supervisor, lo define como «no Listo». Pendiente de acordar con Reyes.",
    strict=False,
)
def test_i2_coincide_con_el_dataset():
    esperados = cargar_dataset()["indicadores_esperados"]
    for pid, proyecto in _supervision_del_frontend().items():
        assert proyecto["indicadores"]["I2"] == esperados[pid]["I2"]
