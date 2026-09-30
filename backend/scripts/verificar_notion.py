"""EN-002: verifica el acceso a la base demo con la Notion API 2025-09-03."""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")
HEADERS = {
    "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}
BASE = "https://api.notion.com/v1"
ESPERADAS = {"Tarea": "title", "Responsable": "people", "Estado": "status", "Fecha límite": "date"}
codigos = {}

def llamar(clave, metodo, ruta, **kw):
    r = requests.request(metodo, BASE + ruta, headers=HEADERS, timeout=20, **kw)
    codigos[clave] = r.status_code
    print(f"{metodo} {ruta} -> HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()

db = llamar("database", "GET", f"/databases/{os.environ['NOTION_DATABASE_ID']}")
ds_id = db["data_sources"][0]["id"]
ds = llamar("data_source", "GET", f"/data_sources/{ds_id}")
filas = llamar("query", "POST", f"/data_sources/{ds_id}/query", json={"page_size": 5})

props = {n: p["type"] for n, p in ds["properties"].items()}
evidencia = {
    "notion_version": "2025-09-03",
    "http": codigos,
    "propiedades": props,
    "chequeo": {k: "ok" if props.get(k) == v else f"falta ({v})" for k, v in ESPERADAS.items()},
    "filas_leidas": len(filas["results"]),
}
print(json.dumps(evidencia, ensure_ascii=False, indent=2))
salida = RAIZ / "docs" / "sprint1" / "evidencias" / "EN-002_notion.json"
salida.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding="utf-8")