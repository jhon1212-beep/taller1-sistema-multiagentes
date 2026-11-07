"""Arranque local de la API con SQLite (sin PostgreSQL) para ensayar la carga. Solo pruebas: la base se borra en cada arranque."""
import os
import tempfile
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SP = Path(tempfile.gettempdir())
os.environ["DATABASE_URL"] = f"sqlite:///{(SP / 'carga.db').as_posix()}"
os.environ["JWT_SECRET"] = "clave-solo-para-pruebas-de-carga-locales-0123456789"
sys.path.insert(0, str(RAIZ / "backend"))

import bcrypt
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def _funciones_sqlite(conexion, _):
    # PostgreSQL tiene btrim; SQLite no. Se registra para que valide el CHECK.
    conexion.create_function("btrim", 1, lambda s: s.strip() if s is not None else None)


from app.compartido.db import obtener_engine
from app.compartido.modelos_orm import Base, Docente
from sqlalchemy.orm import Session

(SP / "carga.db").unlink(missing_ok=True)
Base.metadata.create_all(obtener_engine())
with Session(obtener_engine()) as s:
    s.add(Docente(
        nombre="Docente Carga",
        correo="carga@prueba.local",
        password_hash=bcrypt.hashpw(b"CargaLocal-2026", bcrypt.gensalt()).decode(),
        activo=True,
    ))
    s.commit()

import uvicorn

uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
