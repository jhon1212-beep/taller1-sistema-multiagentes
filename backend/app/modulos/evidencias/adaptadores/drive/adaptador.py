# -*- coding: utf-8 -*-
"""TA-014 · Adaptador real de Google Drive (puerto FuenteEvidencia)."""
from __future__ import annotations

import os
from app.modulos.evidencias.adaptadores.drive.cliente import DriveClient
from app.modulos.evidencias.dominio import EvidenciaDrive

def _normalizar_archivo(archivo: dict, proyecto_id: int) -> EvidenciaDrive:
    return EvidenciaDrive(
        fuente="drive",
        id_externo=archivo["id"],
        autor=archivo.get("editor") or "desconocido",
        fecha=archivo.get("fecha"),
        descripcion=archivo.get("nombre") or "",
        proyecto_id=proyecto_id,
        tipo_archivo=archivo.get("tipo"),
    )

class FuenteEvidenciaDrive:
    """Puede lanzar DriveError; quien la use decide cómo manejarlo."""
    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = None,
        desde: str | None = None,
    ) -> list[EvidenciaDrive]:
        cliente = DriveClient(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
        crudos = cliente.archivos_de_carpeta(referencia, maximo=limite)
        return [_normalizar_archivo(a, proyecto_id) for a in crudos]