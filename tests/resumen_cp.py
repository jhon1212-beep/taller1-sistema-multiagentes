# -*- coding: utf-8 -*-
"""TA-049 · Resume el reporte JUnit de CP-12 a CP-19 como tabla Markdown.

El CI lo escribe en el resumen del job (GITHUB_STEP_SUMMARY), de modo que cada caso
del plan aparece en su propia fila con su resultado. Termina con código 1 si algún
caso falló o no se ejecutó (un CP que falta cuenta como fallo).

    python tests/resumen_cp.py test-results/cp12-cp19.xml >> "$GITHUB_STEP_SUMMARY"
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET

ESPERADOS = [f"CP-{n}" for n in range(12, 20)]


def leer(ruta: str) -> dict[str, dict]:
    """CP -> {resultado, tiempo, prueba}, a partir de los testcase del JUnit."""
    casos: dict[str, dict] = {}
    for caso in ET.parse(ruta).getroot().iter("testcase"):
        coincide = re.search(r"test_cp(\d+)_", caso.get("name", ""))
        if not coincide:
            continue
        if caso.find("failure") is not None or caso.find("error") is not None:
            resultado = "FAIL"
        elif caso.find("skipped") is not None:
            resultado = "OMITIDO"
        else:
            resultado = "PASS"
        casos[f"CP-{coincide.group(1)}"] = {
            "resultado": resultado,
            "tiempo": float(caso.get("time", 0)),
            "prueba": caso.get("name"),
        }
    return casos


def resumir(ruta: str) -> tuple[str, bool]:
    """Devuelve (tabla Markdown, True si los ocho CP pasaron)."""
    casos = leer(ruta)
    filas = ["| CP | Prueba | Resultado | Tiempo |", "|---|---|---|---:|"]
    for cp in ESPERADOS:
        c = casos.get(cp)
        if c is None:
            filas.append(f"| {cp} | (no se ejecutó) | FAIL | — |")
        else:
            filas.append(f"| {cp} | `{c['prueba']}` | {c['resultado']} | {c['tiempo']:.2f} s |")
    correctos = sum(1 for cp in ESPERADOS if casos.get(cp, {}).get("resultado") == "PASS")
    titulo = f"### TA-049 · CP-12 a CP-19: {correctos} de {len(ESPERADOS)} en verde\n"
    return titulo + "\n".join(filas) + "\n", correctos == len(ESPERADOS)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python tests/resumen_cp.py <junit.xml>")
    tabla, todo_bien = resumir(sys.argv[1])
    print(tabla)
    sys.exit(0 if todo_bien else 1)
