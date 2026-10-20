"""TA-019: pruebas del motor I1-I4 / R1-R4 (CP-11: coincidencia con la hoja de TA-017)."""

import json
from pathlib import Path

import pytest

from app.modulos.supervision.motor_indicadores import (
    calcular_indicadores,
    evaluar,
    evaluar_reglas,
)

DATASET = Path(__file__).parent.parent / "fixtures" / "ta017_dataset_ejemplo.json"
CORTE = "2026-10-12T23:59:59-05:00"


def tarea(id_, estado, limite=None, fecha="2026-10-10T10:00:00Z"):
    return {"fuente": "notion", "id_externo": id_, "fecha": fecha, "estado": estado,
            "fecha_limite": limite, "autor": "x", "descripcion": "", "proyecto_id": 1}


def test_cp11_coincide_con_la_hoja():
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    res = evaluar(datos["evidencias"], datos["fecha_corte"])
    esperado = datos["esperado"]
    assert res["indicadores"] == esperado["indicadores"]
    assert sorted((a["regla"], a["evidencia_ids"][0]) for a in res["alertas"]) == sorted(
        tuple(x) for x in esperado["alertas"])


def test_la_fecha_de_corte_es_configurable():
    datos = json.loads(DATASET.read_text(encoding="utf-8"))["evidencias"]
    # Con un corte anterior, ya no hay vencidas ni evidencias "futuras".
    assert calcular_indicadores(datos, "2026-10-03T00:00:00Z")["I3"] == 0
    # Con un corte posterior, el commit "futuro" cuenta y R3 desaparece.
    assert "R3" not in {a["regla"] for a in evaluar_reglas(datos, "2026-10-21T00:00:00Z")}


def test_sin_tareas_i1_i2_son_none():
    ind = calcular_indicadores([], CORTE)
    assert ind == {"I1": None, "I2": None, "I3": 0, "I4": None}


def test_limite_el_mismo_dia_del_corte_no_esta_vencida():
    assert calcular_indicadores([tarea("a", "En curso", "2026-10-12")], CORTE)["I3"] == 0
    assert calcular_indicadores([tarea("a", "En curso", "2026-10-11")], CORTE)["I3"] == 1


def test_sin_actividad_genera_r3_y_r4_sin_evidencia_asociada():
    reglas = {a["regla"]: a for a in evaluar_reglas([], CORTE)}
    assert set(reglas) == {"R3", "R4"}
    assert reglas["R3"]["evidencia_ids"] == []


def test_fecha_de_corte_invalida():
    with pytest.raises(ValueError):
        calcular_indicadores([], "2026-10-12")
    with pytest.raises(ValueError):
        evaluar_reglas([], "2026-10-12T23:59:59")


def test_acepta_evidencias_dataclass():
    from app.modulos.evidencias.dominio import EvidenciaNotion
    ev = EvidenciaNotion("notion", "p1", "x", "2026-10-10T10:00:00Z", "t", 1, "Listo", None)
    assert calcular_indicadores([ev], CORTE)["I1"] == 100.0
