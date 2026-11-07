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


def token_para_base(database_id: str) -> str:
    """Token de Notion para una base concreta.

    Una integración interna de Notion solo ve su propio espacio de trabajo. Si
    un equipo tiene su base en otro espacio, crea allí su integración y su
    token se registra en NOTION_TOKENS (JSON «id de base: token», sin guiones
    en el id). Las bases que no estén en NOTION_TOKENS usan NOTION_TOKEN.
    """
    por_base = os.getenv("NOTION_TOKENS", "").strip()
    if por_base:
        try:
            tokens = {k.replace("-", "").lower(): v for k, v in json.loads(por_base).items()}
        except (ValueError, AttributeError) as err:
            raise NotionError("NOTION_TOKENS debe ser un JSON {\"id de base\": \"token\"}.") from err
        token = tokens.get((database_id or "").replace("-", "").lower())
        if token:
            return str(token).strip()
    return cargar_config()["token"]


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


# Otras bases de Notion usan otros nombres de columna (por ejemplo, la plantilla
# en inglés: Name, Assignee, Status, Due). Primero se busca el nombre de
# nuestra base y sus equivalentes; si ninguno existe, la primera propiedad del
# tipo correcto. Así el agente lee la base de cualquier equipo.
NOMBRES_RESPONSABLE = (PROP_RESPONSABLE, "Responsables", "Asignado", "Asignados",
                       "Encargado", "Assignee", "Assignees", "Assign", "Owner", "Person")
NOMBRES_ESTADO = (PROP_ESTADO, "Estatus", "Status", "State")
NOMBRES_FECHA_LIMITE = (PROP_FECHA_LIMITE, "Fecha limite", "Fecha de entrega", "Vencimiento",
                        "Fecha", "Due", "Due date", "Deadline", "Date")

# Estados equivalentes a los 3 del modelo de datos (Sin empezar, En curso, Listo).
# Se comparan en minúsculas y sin tildes. Un estado desconocido queda en None.
ESTADOS = {
    "Listo": ("listo", "done", "complete", "completed", "completado", "completada",
              "terminado", "terminada", "hecho", "finalizado", "finalizada", "cerrado"),
    "En curso": ("en curso", "in progress", "doing", "en progreso", "en proceso",
                 "haciendo", "en revision", "in review", "review"),
    "Sin empezar": ("sin empezar", "not started", "to do", "todo", "to-do", "por hacer",
                    "pendiente", "backlog", "nuevo", "no iniciado"),
}


def _sin_tildes(texto: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar_estado(nombre: str | None) -> str | None:
    """«Done», «In progress», «Por hacer»… -> «Listo», «En curso», «Sin empezar»."""
    if not nombre:
        return None
    clave = _sin_tildes(nombre).strip().lower()
    for canonico, sinonimos in ESTADOS.items():
        if clave in sinonimos:
            return canonico
    return None


def _propiedad(props: dict, nombres: tuple[str, ...], tipos: tuple[str, ...]) -> dict:
    """Propiedad por nombre preferido (sin distinguir mayúsculas) o, si no, por tipo."""
    por_nombre = {_sin_tildes(k).lower(): v for k, v in props.items()}
    for nombre in nombres:
        valor = por_nombre.get(_sin_tildes(nombre).lower())
        if valor is not None and valor.get("type", tipos[0]) in tipos:
            return valor
    for tipo in tipos:
        for valor in props.values():
            if valor.get("type") == tipo:
                return valor
    return {}


def _normalizar_pagina(pagina: dict) -> dict:
    """Página de Notion -> dict plano con las 4 propiedades + fecha de edición."""
    props = pagina.get("properties", {})

    titulo_prop = props.get(PROP_TAREA) or _propiedad(props, (), ("title",))
    titulo = "".join(t.get("plain_text", "") for t in titulo_prop.get("title", []))

    personas = _propiedad(props, NOMBRES_RESPONSABLE, ("people",)).get("people", [])
    nombres = [p.get("name") for p in personas if p.get("name")]

    estado_prop = _propiedad(props, NOMBRES_ESTADO, ("status", "select"))
    estado_crudo = (estado_prop.get("status") or estado_prop.get("select") or {}).get("name")

    fecha_prop = _propiedad(props, NOMBRES_FECHA_LIMITE, ("date",))
    fecha_limite = (fecha_prop.get("date") or {}).get("start")

    return {
        "id": pagina.get("id"),
        "tarea": titulo,
        "responsable": ", ".join(nombres) if nombres else None,
        "estado": normalizar_estado(estado_crudo),
        "fecha_limite": fecha_limite,
        "editada": pagina.get("last_edited_time"),
    }
