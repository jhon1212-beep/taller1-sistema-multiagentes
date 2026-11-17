"""TA-045: el contrato OpenAPI versionado coincide con la API y describe la supervisión.

Si esta prueba falla tras cambiar una ruta, regenerar el contrato con
`python backend/scripts/exportar_openapi.py` y subir docs/api/openapi.json.
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from app.main import app  # noqa: E402

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def test_el_contrato_versionado_esta_al_dia():
    """Mismas rutas, mismos métodos y mismos esquemas que la API en ejecución.

    Se compara la estructura y no el JSON byte a byte: otra versión de Pydantic
    puede cambiar detalles de formato sin que cambie el contrato.
    """
    versionado, vivo = json.loads(CONTRATO.read_text(encoding="utf-8")), app.openapi()
    rutas = lambda c: {(r, m) for r, ops in c["paths"].items() for m in ops}  # noqa: E731
    assert rutas(versionado) == rutas(vivo)
    assert set(versionado["components"]["schemas"]) == set(vivo["components"]["schemas"])


@pytest.mark.parametrize(("metodo", "ruta", "esquema"), [
    ("post", "/proyectos/{proyecto_id}/consolidacion", "ConsolidacionOut"),
    ("get", "/proyectos/{proyecto_id}/indicadores", "IndicadoresCorteOut"),
    ("get", "/proyectos/{proyecto_id}/alertas", "AlertasCorteOut"),
    ("get", "/proyectos/{proyecto_id}/historial", "HistorialOut"),
])
def test_las_rutas_de_supervision_declaran_su_respuesta(metodo, ruta, esquema):
    respuesta = app.openapi()["paths"][ruta][metodo]["responses"]["200"]["content"]["application/json"]
    assert respuesta["schema"] == {"$ref": f"#/components/schemas/{esquema}"}


def test_cada_alerta_documenta_su_evidencia_de_origen():
    esquemas = app.openapi()["components"]["schemas"]
    assert "evidencia" in esquemas["AlertaConEvidenciaOut"]["properties"]
    assert {"id_externo", "descripcion", "fuente"} <= set(esquemas["EvidenciaOut"]["required"])
