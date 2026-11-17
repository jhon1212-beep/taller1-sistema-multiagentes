"""TA-045: exporta el contrato OpenAPI del backend a docs/api/openapi.json.

El frontend (y quien integre con la API) lee ahí las rutas, parámetros y
formas de respuesta sin levantar el servidor. Se vuelve a ejecutar cada vez
que cambia una ruta; el archivo queda versionado junto al código.

Uso, desde la raíz del repositorio:
    python backend/scripts/exportar_openapi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from app.main import app  # noqa: E402

DESTINO = RAIZ / "docs" / "api" / "openapi.json"


def main() -> None:
    contrato = app.openapi()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(contrato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rutas = sorted(contrato["paths"])
    print(f"Contrato OpenAPI {contrato['info']['version']} con {len(rutas)} rutas -> {DESTINO.relative_to(RAIZ)}")
    for ruta in rutas:
        print("  ", ", ".join(m.upper() for m in contrato["paths"][ruta]), ruta)


if __name__ == "__main__":
    main()
