"""TA-019 · Pruebas del motor de indicadores (I1–I4) y reglas (R1–R4).

Los valores esperados del dataset demo están calculados a mano a partir de
los datos de TA-017 (ver docs/sprint1/TA-019.md), no tomados del generador.
"""
from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.evidencias.dataset import cargar_dataset
from app.modulos.evidencias.dominio import Evidencia, EvidenciaDrive, EvidenciaNotion
from app.modulos.supervision.motor import calcular_indicadores, evaluar, evaluar_reglas

CORTE = "2026-10-13T04:59:59Z"


def _tarea(n, estado, editada, limite):
    return EvidenciaNotion("notion", f"t{n}", "x", editada, f"tarea {n}", 1, estado=estado, fecha_limite=limite)


def _ids(alertas, regla):
    return {i for a in alertas if a["regla"] == regla for i in a["evidencia_ids"]}


def _demo(pid):
    return FuenteEvidenciaDataset().obtener_evidencias("x", pid)


# --- dataset demo -------------------------------------------------------

def test_proyecto_1_indicadores():
    ind, _ = evaluar(_demo(1), CORTE)
    assert ind == {"I1": 40.0, "I2": 30.0, "I3": 4, "I4": 0}  # 8/20, 6/20, tareas 9/12/15/16


def test_proyecto_1_alertas():
    _, alertas = evaluar(_demo(1), CORTE)
    assert _ids(alertas, "R1") == {"tarea-p1-09", "tarea-p1-12", "tarea-p1-15", "tarea-p1-16"}
    assert _ids(alertas, "R2") == {"tarea-p1-09", "tarea-p1-10"}
    assert _ids(alertas, "R3") == set() and _ids(alertas, "R4") == set()


def test_proyecto_2_indicadores():
    ind, _ = evaluar(_demo(2), CORTE)
    assert ind == {"I1": 37.5, "I2": 25.0, "I3": 2, "I4": 7}  # 3/8, 2/8, tareas 4 y 7, último commit 05/10


def test_proyecto_2_alertas():
    _, alertas = evaluar(_demo(2), CORTE)
    assert _ids(alertas, "R1") == {"tarea-p2-04", "tarea-p2-07"}
    assert _ids(alertas, "R2") == {"tarea-p2-04", "tarea-p2-05", "tarea-p2-06"}
    assert len(_ids(alertas, "R3")) == 1 and len(_ids(alertas, "R4")) == 1


def test_r3_y_r4_enlazan_a_la_evidencia_mas_reciente_de_su_fuente():
    evs = _demo(2)
    _, alertas = evaluar(evs, CORTE)
    ultimo = lambda fuente: max((e for e in evs if e.fuente == fuente), key=lambda e: e.fecha).id_externo
    assert _ids(alertas, "R3") == {ultimo("github")}
    assert _ids(alertas, "R4") == {ultimo("drive")}


def test_el_json_del_dataset_coincide_con_el_motor():
    datos = cargar_dataset()
    for pid in (1, 2):
        ind, alertas = evaluar(_demo(pid), datos["fecha_corte"])
        assert datos["indicadores_esperados"][str(pid)] == ind
        esperadas = {(a["regla"], a["evidencia_id"]) for a in datos["alertas_esperadas"][str(pid)]}
        assert esperadas == {(a["regla"], a["evidencia_ids"][0]) for a in alertas}


def test_toda_alerta_tiene_evidencia_de_origen():
    ids = {e.id_externo for e in _demo(2)}
    for a in evaluar(_demo(2), CORTE)[1]:
        assert a["evidencia_ids"] and set(a["evidencia_ids"]) <= ids  # RN-003


# --- casos límite --------------------------------------------------------

def test_sin_tareas_i1_e_i2_son_none():
    commit = Evidencia("github", "c1", "a", "2026-10-12T10:00:00Z", "m", 1)
    ind = calcular_indicadores([commit], CORTE)
    assert ind["I1"] is None and ind["I2"] is None and ind["I3"] == 0


def test_sin_evidencias_i4_es_none_y_no_hay_alertas():
    assert calcular_indicadores([], CORTE)["I4"] is None
    assert evaluar_reglas([], CORTE) == []


def test_las_evidencias_posteriores_al_corte_se_ignoran():
    futura = _tarea(1, "En curso", "2026-10-14T10:00:00Z", "2026-10-01")
    assert evaluar([futura], CORTE) == ({"I1": None, "I2": None, "I3": 0, "I4": None}, [])


def test_r1_no_se_dispara_con_tarea_lista_ni_sin_fecha_limite():
    evs = [_tarea(1, "Listo", "2026-10-01T10:00:00Z", "2026-10-01"),
           _tarea(2, "En curso", "2026-10-12T10:00:00Z", None)]
    assert _ids(evaluar_reglas(evs, CORTE), "R1") == set()


def test_r2_umbral_de_7_dias():
    justo = _tarea(1, "En curso", "2026-10-06T04:59:59Z", "2026-11-01")   # exactamente 7 días
    pasado = _tarea(2, "En curso", "2026-10-06T04:59:58Z", "2026-11-01")  # 1 segundo más
    assert _ids(evaluar_reglas([justo, pasado], CORTE), "R2") == {"t2"}


def test_r4_umbral_de_14_dias_y_fuente_vacia():
    doc = EvidenciaDrive("drive", "d1", "x", "2026-09-29T04:59:58Z", "doc", 1, tipo_archivo="pdf")
    assert _ids(evaluar_reglas([doc], CORTE), "R4") == {"d1"}
    ok = EvidenciaDrive("drive", "d2", "x", "2026-09-29T04:59:59Z", "doc", 1, tipo_archivo="pdf")
    assert _ids(evaluar_reglas([ok], CORTE), "R4") == set()
    assert _ids(evaluar_reglas([_tarea(1, "Listo", "2026-10-01T00:00:00Z", None)], CORTE), "R3") == set()
