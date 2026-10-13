# -*- coding: utf-8 -*-
"""EN-002 / TA-007 · Cliente de la Notion API (solo lectura).

Usa la versión 2025-09-03: una base de datos contiene uno o más
data sources y las tareas se consultan en /data_sources/{id}/query
(hallazgo documentado en docs/sprint1/EN-002.md).

Sin dependencias externas: solo la librería estándar, igual que el
cliente de GitHub. Nunca incluye el token en los mensajes de error.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.compartido.config import RAIZ  # noqa: F401  (carga el .env al importar)

API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"

PROP_TAREA = "Tarea"
PROP_RESPONSABLE = "Responsable"
PROP_ESTADO = "Estado"
PROP_FECHA_LIMITE = "Fecha límite"


class NotionError(Exception):
    """Fallo genérico de la API (red, 404, 500...)."""


class NotionAuthError(NotionError):
    """Token inválido o sin acceso a la base (HTTP 401/403)."""


def cargar_config() -> dict:
    """Lee NOTION_TOKEN y NOTION_DATABASE_ID del entorno (.env ya cargado)."""
    return {
        "token": os.getenv("NOTION_TOKEN", "").strip(),
        "database_id": os.getenv("NOTION_DATABASE_ID", "").strip(),
    }


class NotionClient:
    def __init__(self, token: str, api_url: str = API_URL, timeout: int = 20):
        self.token = (token or "").strip()
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    # -- interno ----------------------------------------------------------
    def _request(self, metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
        if not self.token:
            raise NotionAuthError("Falta NOTION_TOKEN.")
        datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
        peticion = urllib.request.Request(
            f"{self.api_url}{ruta}",
            data=datos,
            method=metodo,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                raise NotionAuthError(
                    f"Notion rechazó el acceso (HTTP {err.code}) en {ruta}."
                ) from err
            raise NotionError(f"HTTP {err.code} al consultar Notion en {ruta}.") from err
        except urllib.error.URLError as err:
            raise NotionError(f"Error de red al consultar Notion: {err.reason}") from err

    # -- endpoints --------------------------------------------------------
    def data_source_id(self, database_id: str) -> str:
        """GET /databases/{id} -> id del primer data source."""
        base = self._request("GET", f"/databases/{database_id}")
        fuentes = base.get("data_sources") or []
        if not fuentes:
            raise NotionError("La base de Notion no tiene data sources.")
        return fuentes[0]["id"]

    def tareas(self, database_id: str, desde: str | None = None,
               maximo: int | None = None) -> list[dict]:
        """POST /data_sources/{id}/query (paginado) -> tareas normalizadas."""
        ds_id = self.data_source_id(database_id)
        cuerpo: dict = {"page_size": min(maximo or 100, 100)}
        if desde:
            cuerpo["filter"] = {
                "timestamp": "last_edited_time",
                "last_edited_time": {"on_or_after": desde},
            }
        salida: list[dict] = []
        while True:
            respuesta = self._request("POST", f"/data_sources/{ds_id}/query", cuerpo)
            salida.extend(_normalizar_pagina(p) for p in respuesta.get("results", []))
            if maximo is not None and len(salida) >= maximo:
                return salida[:maximo]
            if not respuesta.get("has_more"):
                return salida
            cuerpo["start_cursor"] = respuesta["next_cursor"]


def _normalizar_pagina(pagina: dict) -> dict:
    """Página de Notion -> dict plano con las 4 propiedades + fecha de edición."""
    props = pagina.get("properties", {})

    titulo = "".join(
        t.get("plain_text", "") for t in props.get(PROP_TAREA, {}).get("title", [])
    )
    personas = props.get(PROP_RESPONSABLE, {}).get("people", [])
    nombres = [p.get("name") for p in personas if p.get("name")]
    estado = (props.get(PROP_ESTADO, {}).get("status") or {}).get("name")
    fecha_limite = (props.get(PROP_FECHA_LIMITE, {}).get("date") or {}).get("start")

    return {
        "id": pagina.get("id"),
        "tarea": titulo,
        "responsable": ", ".join(nombres) if nombres else None,
        "estado": estado,
        "fecha_limite": fecha_limite,
        "editada": pagina.get("last_edited_time"),
    }
