"""Conexión a PostgreSQL con SQLAlchemy. El motor se crea al usarlo, no al importar."""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.compartido.config import obtener_database_url


@lru_cache
def obtener_engine():
    return create_engine(obtener_database_url(), pool_pre_ping=True)


def obtener_sesion():
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar."""
    sesion = sessionmaker(bind=obtener_engine(), autoflush=False)()
    try:
        yield sesion
    finally:
        sesion.close()
