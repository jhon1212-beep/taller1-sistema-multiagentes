# -*- coding: utf-8 -*-
"""TA-039 · Levanta la API real con los datos de demostración en PostgreSQL.

Sirve para probar el frontend contra el backend de verdad cuando no hay una
base desplegada ni credenciales de Notion:

  1. Siembra (de forma idempotente) los 5 docentes de la demostración, los dos
     proyectos del dataset de TA-017 y sus 76 evidencias, con todos sus campos.
  2. Arranca FastAPI en 127.0.0.1:8000.
  3. Sustituye SOLO el adaptador de Notion de /proyectos/{id}/tareas por el
     dataset controlado (FuenteEvidenciaDataset), porque la ruta consulta Notion
     en vivo y aquí no hay token. Login, proyectos, commits y documentos son los
     de producción: salen de PostgreSQL.

Variables de entorno: DATABASE_URL y JWT_SECRET (obligatorias); CORS_ORIGINS si
el frontend corre en otro puerto que el 5173. La base debe tener las migraciones
aplicadas (cd backend && alembic upgrade head).

    python backend/scripts/demo_api_real.py            # siembra y arranca
    python backend/scripts/demo_api_real.py --solo-sembrar
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

import bcrypt  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido.db import obtener_engine  # noqa: E402
from app.compartido.modelos_orm import Docente, Evidencia, Fuente, Integrante, Proyecto  # noqa: E402
from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402

CLAVE_DEMO = "DemoDocente2026!"  # misma que frontend/src/datos/demo.js y el docente falso (AR-04)

PROYECTOS = [  # idénticos a PROYECTOS_INICIALES de frontend/src/datos/demo.js
    {
        "nombre": "Seguimiento académico", "curso": "Taller Integrador 1",
        "integrantes": ["Ana Torres", "Luis Vega", "Marta Ruiz", "Diego Paz"],
        "github": "https://github.com/demo/seguimiento", "notion": "https://notion.so/demo-backlog",
        "drive": "https://drive.google.com/drive/folders/demo", "selector": "h1",
    },
    {
        "nombre": "Biblioteca digital", "curso": "Ingeniería de Software",
        "integrantes": ["Elena Ríos", "Carlos León"],
        "github": "https://github.com/demo/biblioteca", "notion": "https://notion.so/demo-biblioteca",
        "drive": "https://drive.google.com/drive/folders/demo-biblioteca", "selector": "#catalogo",
    },
]


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def sembrar() -> None:
    dataset = cargar_dataset()
    ahora = datetime.now(timezone.utc)
    with Session(obtener_engine()) as s:
        for i in range(1, 6):
            correo = f"docente{i}@demo.test"
            if s.scalar(select(Docente).where(Docente.correo == correo)) is None:
                s.add(Docente(
                    nombre=f"Docente demo {i}", correo=correo, activo=True,
                    password_hash=bcrypt.hashpw(CLAVE_DEMO.encode(), bcrypt.gensalt()).decode(),
                ))
        s.flush()
        docente = s.scalar(select(Docente).where(Docente.correo == "docente1@demo.test"))

        por_nombre: dict[str, Proyecto] = {}
        for d in PROYECTOS:
            p = s.scalar(select(Proyecto).where(Proyecto.nombre == d["nombre"]))
            if p is None:
                p = Proyecto(
                    docente_id=docente.id, nombre=d["nombre"], curso=d["curso"],
                    fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
                    url_publica="https://example.org", elemento_verificar=d["selector"], activo=True,
                )
                s.add(p)
                s.flush()
                s.add_all(Integrante(proyecto_id=p.id, nombre=n) for n in d["integrantes"])
                for tipo in ("github", "notion", "drive"):
                    s.add(Fuente(proyecto_id=p.id, tipo=tipo, referencia=d[tipo], estado="ok",
                                 ultima_sincronizacion=ahora))
            por_nombre[d["nombre"]] = p
        s.flush()

        id_dataset = {p["id"]: por_nombre[p["nombre"]].id for p in dataset["proyectos"]}
        nuevas = 0
        for e in dataset["evidencias"]:
            pid = id_dataset[e["proyecto_id"]]
            fuente = s.scalar(select(Fuente).where(Fuente.proyecto_id == pid, Fuente.tipo == e["fuente"]))
            existe = s.scalar(select(Evidencia.id).where(
                Evidencia.fuente_id == fuente.id, Evidencia.id_externo == e["id_externo"]))
            if existe is None:
                limite = e.get("fecha_limite")
                s.add(Evidencia(
                    proyecto_id=pid, fuente_id=fuente.id, id_externo=e["id_externo"], autor=e["autor"],
                    fecha=_fecha(e["fecha"]), descripcion=e["descripcion"], estado=e.get("estado"),
                    fecha_limite=date.fromisoformat(limite) if limite else None,
                    tipo_archivo=e.get("tipo_archivo"),
                ))
                nuevas += 1
        s.commit()
    print(f"Sembrado: 5 docentes, {len(PROYECTOS)} proyectos, {nuevas} evidencias nuevas.")


def crear_app():
    from app.main import app
    from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
    from app.modulos.evidencias.rutas_tareas import obtener_fuente_tareas

    app.dependency_overrides[obtener_fuente_tareas] = lambda: FuenteEvidenciaDataset("notion")
    return app


if __name__ == "__main__":
    sembrar()
    if "--solo-sembrar" not in sys.argv:
        import uvicorn

        uvicorn.run(crear_app(), host="127.0.0.1", port=8000, log_level="warning")
