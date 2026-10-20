"""HU-003 / HU-005: los datos de demostración del frontend coinciden con el dataset de TA-017."""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATASET = RAIZ / "backend/app/modulos/evidencias/dataset/proyecto_demo.json"
DEMO_JS = RAIZ / "frontend/src/datos/demo_dataset.js"


def _constante(nombre: str) -> list[dict]:
    texto = DEMO_JS.read_text(encoding="utf-8")
    cuerpo = re.search(rf"export const {nombre} = (\[.*?\n\])", texto, re.S).group(1)
    return json.loads(cuerpo)


def _evidencias(fuente: str) -> list[dict]:
    datos = json.loads(DATASET.read_text(encoding="utf-8"))
    return [e for e in datos["evidencias"] if e["fuente"] == fuente and e["proyecto_id"] == 1]


def test_commits_del_frontend_coinciden_con_el_dataset():
    pantalla, origen = _constante("COMMITS_DATASET"), _evidencias("github")
    assert len(pantalla) == len(origen) == 20
    for fila, ev in zip(pantalla, origen):
        assert fila["autor"] == ev["autor"]
        assert fila["mensaje"] == ev["descripcion"]
        assert fila["sha"] == ev["id_externo"][:7]
        assert fila["fecha"] == ev["fecha"][:16].replace("T", " ")


def test_documentos_del_frontend_coinciden_con_el_dataset():
    pantalla, origen = _constante("DOCUMENTOS_DATASET"), _evidencias("drive")
    assert len(pantalla) == len(origen) == 10
    for fila, ev in zip(pantalla, origen):
        assert fila["nombre"] == ev["descripcion"]
        assert fila["editor"] == ev["autor"]
        assert fila["modificado"] == ev["fecha"][:16].replace("T", " ")
