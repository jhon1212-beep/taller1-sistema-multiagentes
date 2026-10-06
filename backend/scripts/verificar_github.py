"""EN-001: guarda la respuesta 200 de GET /rate_limit con sus cabeceras."""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from app.modulos.evidencias.adaptadores.github.cliente import GitHubClient, cargar_env  # noqa: E402

env = cargar_env()
cliente = GitHubClient(
    token=env.get("GITHUB_TOKEN"),
    org=env.get("GITHUB_ORG"),
    api_url=env.get("GITHUB_API_URL", "https://api.github.com"),
)
url = f"{cliente.api_url}/rate_limit"
peticion = urllib.request.Request(url, headers=cliente._headers(), method="GET")

with urllib.request.urlopen(peticion, timeout=20) as resp:
    estado = resp.status
    cabeceras = dict(resp.headers)
    cuerpo = json.loads(resp.read().decode("utf-8"))

nucleo = cuerpo["resources"]["core"]
lineas = [
    f"Fecha: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
    f"GET {url} -> HTTP {estado}",
    f"Autenticado: {bool(cliente.token)}",
    f"core: limite={nucleo['limit']} restantes={nucleo['remaining']}",
    "",
    "Cabeceras de la respuesta:",
    *[f"  {k}: {v}" for k, v in sorted(cabeceras.items())],
]
texto = "\n".join(lineas)
print(texto)

salida = RAIZ / "docs" / "sprint1" / "evidencias" / "EN-001_respuesta_200.txt"
salida.write_text(texto + "\n", encoding="utf-8")
print(f"\nGuardado en: {salida}")