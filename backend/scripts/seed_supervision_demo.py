"""Prepara un docente y proyecto demo en una base PostgreSQL AISLADA.

Auxiliar para CP6 (no es una migración). No genera cortes automáticamente:
las solicitudes POST /consolidacion de Swagger deben crear los dos cortes.
"""
from __future__ import annotations

import argparse
from datetime import date
from getpass import getpass

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.compartido import modelos_orm as orm
from app.compartido.config import obtener_database_url
from app.modulos.autenticacion.servicio import hashear_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear proyecto demo TA-022 en una base aislada")
    parser.add_argument("--email", required=True, help="Correo de docente de prueba")
    parser.add_argument("--confirm-isolated", action="store_true", help="Confirma base exclusiva de pruebas")
    args = parser.parse_args()
    if not args.confirm_isolated:
        parser.error("Antes de insertar datos, verifica la rama aislada de Neon y agrega --confirm-isolated")

    password = getpass("Clave del docente demo (no se mostrará): ")
    if not password:
        parser.error("La clave no puede estar vacía")
    engine = create_engine(obtener_database_url(), pool_pre_ping=True)
    try:
        with Session(engine) as session:
            existing = session.scalars(select(orm.Docente).where(orm.Docente.correo == args.email)).first()
            if existing is not None:
                print("Ya existe un docente con ese correo. No se hicieron cambios.")
                print("Usa otro correo de prueba para evitar modificar datos existentes.")
                return

            teacher = orm.Docente(
                nombre="Docente demo CP6", correo=args.email,
                password_hash=hashear_password(password),
            )
            session.add(teacher)
            session.flush()
            project = orm.Proyecto(
                docente_id=teacher.id, nombre="Proyecto demo CP6 TA-022",
                curso="TI1", fecha_inicio=date(2026, 9, 21),
                fecha_fin=date(2026, 11, 30),
                url_publica="https://demo.test", elemento_verificar="h1",
            )
            session.add(project)
            session.flush()
            for source in ("github", "notion", "drive"):
                session.add(orm.Fuente(
                    proyecto_id=project.id, tipo=source, referencia="dataset:1",
                ))
            session.commit()
            print("PROYECTO DEMO CREADO")
            print("proyecto_id =", project.id)
            print("correo docente =", args.email)
            print("Fuentes registradas: github, notion, drive (dataset:1)")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
