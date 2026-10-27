# -*- coding: utf-8 -*-
"""TA-021 / TA-047 · Demostración: 2 ejecuciones del workflow (PASS y FAIL) por la API.

Requisitos:
  - PostgreSQL con la migración aplicada y DATABASE_URL definida.
  - La API en marcha con E2E_EJECUTOR=local (o «actions» si hay repositorio remoto).
  - Un sitio al que apuntar (por defecto el frontend en http://127.0.0.1:5173).

Qué hace: siembra un docente de prueba y dos proyectos que solo difieren en
`elemento_verificar` (uno existe en la página, otro no), inicia sesión, llama
POST /validaciones por cada proyecto y muestra las filas guardadas en `validacion`.

Uso:  python backend/scripts/ta021_demo_validacion.py [URL_API] [URL_SITIO]
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido import modelos_orm as orm  # noqa: E402
from app.compartido.db import obtener_engine  # noqa: E402
from app.modulos.autenticacion.servicio import hashear_password  # noqa: E402

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SITIO = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5173"
CORREO, CLAVE = "docente1@demo.test", "DemoDocente2026!"  # cuenta de la demo (frontend/src/datos/demo.js)

PROYECTOS = [
    ("Demo TA-021 · elemento presente", "h1"),
    ("Demo TA-021 · elemento ausente", "#elemento-que-no-existe"),
]


def sembrar() -> list[int]:
    with Session(obtener_engine()) as s:
        docente = s.scalars(select(orm.Docente).where(orm.Docente.correo == CORREO)).first()
        if docente is None:
            docente = orm.Docente(nombre="Docente Demo", correo=CORREO, password_hash=hashear_password(CLAVE))
            s.add(docente)
            s.flush()
        ids = []
        for nombre, elemento in PROYECTOS:
            p = s.scalars(select(orm.Proyecto).where(orm.Proyecto.nombre == nombre)).first()
            if p is None:
                p = orm.Proyecto(
                    docente_id=docente.id, nombre=nombre, curso="Taller Integrador 1",
                    fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
                    url_publica=SITIO, elemento_verificar=elemento,
                )
                s.add(p)
                s.flush()
            ids.append(p.id)
        s.commit()
        return ids


def post(ruta: str, cuerpo: dict, token: str | None = None) -> tuple[int, dict]:
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + ruta, data=json.dumps(cuerpo).encode(), headers=cabeceras, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.status, json.loads(r.read())


def main() -> None:
    ids = sembrar()
    print(f"Proyectos sembrados: {ids}")
    _, login = post("/auth/login", {"correo": CORREO, "password": CLAVE})
    token = login["token"]
    for pid in ids:
        codigo, cuerpo = post("/validaciones", {"proyecto_id": pid}, token)
        print(f"POST /validaciones proyecto={pid} -> HTTP {codigo}")
        print(json.dumps(cuerpo, indent=2, ensure_ascii=False))
    print("\nFilas en la tabla validacion:")
    with Session(obtener_engine()) as s:
        for v in s.scalars(select(orm.Validacion).order_by(orm.Validacion.id)):
            print(
                f"  id={v.id} proyecto={v.proyecto_id} {v.resultado} {v.duracion_ms} ms "
                f"run_id={v.run_id_actions} captura={'sí' if v.captura_url else 'no'} {v.ejecutada_en.isoformat()}"
            )


if __name__ == "__main__":
    main()
