"""Configuración: lee las variables de entorno desde el .env de la raíz del repositorio."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")


def obtener_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "Falta DATABASE_URL. Copia .env.example como .env y completa el valor."
        )
    return url
