"""TA-014: trae los archivos de Drive y los guarda en PostgreSQL."""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from app.compartido.db import obtener_engine
from app.compartido.modelos_orm import Fuente
from app.modulos.evidencias.agentes.agente_drive import agente_drive
from app.modulos.evidencias.dominio import EvidenciaDrive
from app.modulos.evidencias.normalizacion import normalizar
from app.modulos.evidencias.adaptadores.postgres.repositorio import RepositorioEvidenciasSQL

PROYECTO_ID = 1

resultado = agente_drive({
    "carpeta_id": os.environ["GOOGLE_DRIVE_FOLDER_ID"],
    "proyecto_id": PROYECTO_ID,
})

with sessionmaker(bind=obtener_engine())() as sesion:
    fuente = sesion.scalar(
        select(Fuente).where(Fuente.proyecto_id == PROYECTO_ID, Fuente.tipo == "drive")
    )
    
    if resultado["estado_fuente"] == "ok":
        # Reconstruir las entidades de dominio para normalizarlas
        evidencias_dominio = [EvidenciaDrive(**e) for e in resultado["evidencias"]]
        evidencias_normalizadas = normalizar(evidencias_dominio)
        
        # Guardado oficial con el repositorio de TA-010
        repositorio = RepositorioEvidenciasSQL(sesion)
        repositorio.guardar(evidencias_normalizadas)
        
    fuente.estado = resultado["estado_fuente"]
    fuente.ultima_sincronizacion = datetime.now(timezone.utc)
    sesion.commit()

print(f"estado={resultado['estado_fuente']} · evidencias={len(resultado['evidencias'])}")