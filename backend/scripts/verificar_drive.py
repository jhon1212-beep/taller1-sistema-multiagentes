"""EN-004: verifica files.list sobre la carpeta demo de Drive (HTTP 200)."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

ALCANCE = "https://www.googleapis.com/auth/drive.readonly"
ruta = Path(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"].strip())
if not ruta.is_absolute():
    ruta = RAIZ / ruta
carpeta = os.environ["GOOGLE_DRIVE_FOLDER_ID"].strip()

credenciales = service_account.Credentials.from_service_account_file(
    str(ruta), scopes=[ALCANCE]
)
sesion = AuthorizedSession(credenciales)
resp = sesion.get(
    "https://www.googleapis.com/drive/v3/files",
    params={
        "q": f"'{carpeta}' in parents and trashed = false",
        "fields": "files(id,name,mimeType,modifiedTime,lastModifyingUser(displayName))",
        "pageSize": 100,
    },
    timeout=20,
)
print(f"GET /drive/v3/files -> HTTP {resp.status_code}")
resp.raise_for_status()
archivos = resp.json().get("files", [])

evidencia = {
    "api": "Google Drive v3",
    "alcance": ALCANCE,
    "http": {"files.list": resp.status_code},
    "archivos_listados": len(archivos),
    "campos_presentes": sorted({k for a in archivos for k in a}),
}
print(json.dumps(evidencia, ensure_ascii=False, indent=2))

salida = RAIZ / "docs" / "sprint2" / "evidencias" / "EN-004_drive.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding="utf-8")