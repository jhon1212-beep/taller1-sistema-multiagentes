"""TA-017 · Pruebas del dataset controlado del proyecto demo."""
import subprocess
import sys
from collections import Counter
from pathlib import Path

from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.evidencias.dataset import RUTA_DATASET, cargar_dataset
from app.modulos.evidencias.dominio import EvidenciaDrive, EvidenciaNotion

RAIZ = Path(__file__).resolve().parents[2]


def test_volumen_del_proyecto_1():
    por_fuente = Counter(e.fuente for e in FuenteEvidenciaDataset().obtener_evidencias("x", 1))
    assert por_fuente == {"github": 20, "notion": 20, "drive": 10}


def test_notion_y_drive_traen_sus_atributos_propios():
    evs = FuenteEvidenciaDataset().obtener_evidencias("x", 1)
    assert all(isinstance(e, EvidenciaNotion) and e.estado in ("Sin empezar", "En curso", "Listo")
               for e in evs if e.fuente == "notion")
    assert all(isinstance(e, EvidenciaDrive) and e.tipo_archivo for e in evs if e.fuente == "drive")


def test_hay_una_tarea_sin_responsable():
    notion = FuenteEvidenciaDataset("notion").obtener_evidencias("x", 1)
    assert [e.autor for e in notion].count(None) == 1


def test_ids_unicos_y_proyectos_separados():
    todas = FuenteEvidenciaDataset().obtener_evidencias("x", 1) + FuenteEvidenciaDataset().obtener_evidencias("x", 2)
    claves = [(e.fuente, e.id_externo) for e in todas]
    assert len(claves) == len(set(claves))
    assert FuenteEvidenciaDataset().obtener_evidencias("x", 99) == []


def test_filtros_limite_desde_y_fuente():
    f = FuenteEvidenciaDataset("github")
    assert len(f.obtener_evidencias("x", 1, limite=5)) == 5
    assert all(e.fuente == "github" for e in f.obtener_evidencias("x", 1))
    desde = "2026-10-05T00:00:00Z"
    assert all(e.fecha > desde for e in f.obtener_evidencias("x", 1, desde=desde))


def test_alertas_esperadas_por_escenario():
    esperadas = cargar_dataset()["alertas_esperadas"]
    reglas_1 = {a["regla"] for a in esperadas["1"]}
    reglas_2 = {a["regla"] for a in esperadas["2"]}
    assert reglas_1 == {"R1", "R2"}  # activo: sin R3 ni R4
    assert {"R3", "R4"} <= reglas_2  # estancado
    ids = {e.id_externo for e in FuenteEvidenciaDataset().obtener_evidencias("x", 1)}
    assert all(a["evidencia_id"] in ids for a in esperadas["1"])  # RN-003


def test_el_json_coincide_con_el_generador():
    """Si alguien edita el JSON a mano, la prueba falla."""
    sys.path.insert(0, str(RAIZ / "backend" / "scripts"))
    import generar_dataset_demo as g

    assert cargar_dataset() == g.construir()
    assert RUTA_DATASET.exists()
