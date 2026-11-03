"""TA-049: el resumen del CI marca como fallo cualquier CP que falle o falte."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from resumen_cp import ESPERADOS, resumir  # noqa: E402


def junit(tmp_path, casos):
    """casos: {numero_de_cp: None | 'failure' | 'skipped'}"""
    filas = ""
    for numero, problema in casos.items():
        interior = f"<{problema} message='x'/>" if problema else ""
        filas += f'<testcase classname="t" name="test_cp{numero}_caso" time="0.5">{interior}</testcase>'
    ruta = tmp_path / "junit.xml"
    ruta.write_text(f'<testsuites><testsuite name="pytest">{filas}</testsuite></testsuites>', encoding="utf-8")
    return str(ruta)


def test_ocho_casos_en_verde(tmp_path):
    tabla, bien = resumir(junit(tmp_path, {n: None for n in range(12, 20)}))
    assert bien and "8 de 8 en verde" in tabla and tabla.count("| PASS |") == 8


def test_un_caso_fallido_hace_fallar_el_resumen(tmp_path):
    casos = {n: None for n in range(12, 20)}
    casos[17] = "failure"
    tabla, bien = resumir(junit(tmp_path, casos))
    assert not bien and "7 de 8 en verde" in tabla and "| CP-17 |" in tabla and "| FAIL |" in tabla


def test_un_caso_que_falta_cuenta_como_fallo(tmp_path):
    tabla, bien = resumir(junit(tmp_path, {n: None for n in range(12, 19)}))  # sin CP-19
    assert not bien and "(no se ejecutó)" in tabla


def test_un_caso_omitido_no_cuenta_como_verde(tmp_path):
    casos = {n: None for n in range(12, 20)}
    casos[14] = "skipped"
    _, bien = resumir(junit(tmp_path, casos))
    assert not bien


def test_se_esperan_los_cp_12_a_19():
    assert ESPERADOS[0] == "CP-12" and ESPERADOS[-1] == "CP-19" and len(ESPERADOS) == 8
