# -*- coding: utf-8 -*-
"""EN-004 / TA-014 · Cliente de Google Drive API v3 (solo lectura)."""
from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

from app.compartido.config import RAIZ

ALCANCE = "https://www.googleapis.com/auth/drive.readonly"
URL_ARCHIVOS = "https://www.googleapis.com/drive/v3/files"
TIPO_CARPETA = "application/vnd.google-apps.folder"
PROFUNDIDAD_MAXIMA = 3
CARPETAS_MAXIMAS = 50
CAMPOS = (
    "nextPageToken,files(id,name,mimeType,modifiedTime,"
    "lastModifyingUser(displayName,emailAddress))"
)


class DriveError(Exception):
    """Fallo de la API de Drive (credenciales, red, 403, 404...)."""


def _cargar_credenciales(valor: str):
    """Acepta el JSON completo o la ruta al archivo de la cuenta de servicio."""
    valor = (valor or "").strip()
    if not valor:
        raise DriveError("Falta GOOGLE_SERVICE_ACCOUNT_JSON.")
    try:
        if valor.startswith("{"):
            info = json.loads(valor)
        else:
            ruta = Path(valor)
            if not ruta.is_absolute():
                ruta = Path(RAIZ) / ruta
            info = json.loads(ruta.read_text(encoding="utf-8"))
        return service_account.Credentials.from_service_account_info(
            info, scopes=[ALCANCE]
        )
    except (OSError, ValueError) as err:
        raise DriveError(f"Credenciales de Drive inválidas: {err}") from err


class DriveClient:
    def __init__(self, credenciales: str | None = None, timeout: int = 20):
        self.credenciales = credenciales or ""
        self.timeout = timeout
        self._sesion = None  # se crea al primer uso

    def _obtener_sesion(self):
        if self._sesion is None:
            self._sesion = AuthorizedSession(_cargar_credenciales(self.credenciales))
        return self._sesion

    def _listar(self, carpeta_id: str) -> list[dict]:
        """files.list de los hijos directos de una carpeta (todas las páginas)."""
        params = {
            "q": f"'{carpeta_id.replace(chr(39), '')}' in parents and trashed = false",
            "fields": CAMPOS,
            "pageSize": 100,
            "orderBy": "modifiedTime desc",
            # Carpetas dentro de unidades compartidas de un equipo.
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        items: list[dict] = []
        while True:
            try:
                resp = self._obtener_sesion().get(
                    URL_ARCHIVOS, params=params, timeout=self.timeout
                )
            except DriveError:
                raise
            except Exception as err:  # red o autenticación
                raise DriveError(f"Error al consultar Drive: {err}") from err
            if resp.status_code != 200:
                raise DriveError(f"HTTP {resp.status_code} al consultar la carpeta de Drive")
            cuerpo = resp.json()
            items.extend(cuerpo.get("files", []))
            token = cuerpo.get("nextPageToken")
            if not token:
                return items
            params["pageToken"] = token

    def archivos_de_carpeta(self, carpeta_id: str, maximo: int | None = None) -> list[dict]:
        """Documentos de la carpeta y de sus subcarpetas: nombre, último editor, fecha y tipo.

        Los equipos suelen ordenar su documentación en subcarpetas; si solo se
        leyera el primer nivel, R4 daría «carpeta sin cambios» aunque haya
        documentos recientes más adentro. Se recorre hasta PROFUNDIDAD_MAXIMA
        niveles y CARPETAS_MAXIMAS carpetas para acotar las llamadas a la API.
        Las carpetas no cuentan como documentos.
        """
        if not carpeta_id:
            raise DriveError("Falta la referencia de la carpeta de Drive.")
        archivos: list[dict] = []
        pendientes, vistas = [(carpeta_id, 0)], {carpeta_id}
        while pendientes and len(vistas) <= CARPETAS_MAXIMAS:
            actual, nivel = pendientes.pop(0)
            for item in self._listar(actual):
                if item.get("mimeType") == TIPO_CARPETA:
                    hija = item.get("id")
                    if hija and hija not in vistas and nivel < PROFUNDIDAD_MAXIMA:
                        vistas.add(hija)
                        pendientes.append((hija, nivel + 1))
                    continue
                editor = item.get("lastModifyingUser") or {}
                archivos.append({
                    "id": item.get("id") or "",
                    "nombre": item.get("name") or "",
                    "tipo": item.get("mimeType"),
                    "fecha": item.get("modifiedTime"),
                    "editor": editor.get("displayName") or editor.get("emailAddress"),
                })
        archivos.sort(key=lambda a: a.get("fecha") or "", reverse=True)
        return archivos[:maximo] if maximo else archivos
