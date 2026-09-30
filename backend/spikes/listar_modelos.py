"""SP-001: lista los modelos Gemini Flash disponibles para la API key."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

RAIZ = Path(__file__).resolve().parents[2]

# Carga las variables del .env ubicado en la raíz del proyecto.
load_dotenv(RAIZ / ".env", override=True)

# Comprueba que la clave tenga un valor.
api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not api_key:
    raise SystemExit(
        "Falta GEMINI_API_KEY: coloca tu clave real en el archivo .env "
        "de la raíz del proyecto y guarda los cambios."
    )

client = genai.Client(api_key=api_key)

# Obtiene los modelos cuyo nombre contiene 'flash'.
nombres = [
    modelo.name
    for modelo in client.models.list()
    if modelo.name and "flash" in modelo.name.lower()
]

if not nombres:
    raise SystemExit("No se encontraron modelos con 'flash' en su nombre.")

print("\n".join(nombres))

# Guarda el listado como evidencia.
archivo = RAIZ / "docs/sprint1/evidencias/SP-001_modelos.txt"
archivo.parent.mkdir(parents=True, exist_ok=True)
archivo.write_text("\n".join(nombres), encoding="utf-8")

print(f"\nEvidencia guardada en: {archivo}")