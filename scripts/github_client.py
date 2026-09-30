# -*- coding: utf-8 -*-
"""
EN-001 · Cliente de la GitHub API (solo lectura)
Proyecto: Agentes inteligentes para el seguimiento y supervisión de
proyectos de software en entornos académicos.

Soporta HU-001: obtiene commits, ramas, PRs e issues con autor y fecha.
Si la API falla o excede su límite, lanza RateLimitError / GitHubError para
que el agente siga funcionando con los datos de la última sincronización.

Sin dependencias externas: usa solo la librería estándar.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_VERSION = "2022-11-28"
USER_AGENT = "agente-seguimiento-academico/1.0"


# --------------------------------------------------------------------------
# Errores
# --------------------------------------------------------------------------
class GitHubError(Exception):
    """Fallo genérico de la API (red, 404, 500...)."""


class RateLimitError(GitHubError):
    """Límite de peticiones excedido (403/429). Incluye cuándo se restablece."""

    def __init__(self, mensaje: str, reset_epoch: int | None = None):
        super().__init__(mensaje)
        self.reset_epoch = reset_epoch

    @property
    def segundos_para_reset(self) -> int:
        if not self.reset_epoch:
            return 60
        return max(0, int(self.reset_epoch - time.time()))


# --------------------------------------------------------------------------
# Carga de variables de entorno (.env)
# --------------------------------------------------------------------------
def cargar_env(ruta: str | None = None) -> dict:
    """Lee un archivo .env simple (CLAVE=valor). No sobrescribe os.environ."""
    valores = {}
    if ruta is None:
        ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave, _, valor = linea.partition("=")
                valores[clave.strip()] = valor.strip().strip('"').strip("'")
    # las variables reales del sistema tienen prioridad
    for clave in ("GITHUB_TOKEN", "GITHUB_ORG", "GITHUB_API_URL"):
        if os.environ.get(clave):
            valores[clave] = os.environ[clave]
    return valores


# --------------------------------------------------------------------------
# Cliente
# --------------------------------------------------------------------------
class GitHubClient:
    """Cliente de solo lectura de la GitHub REST API v3."""

    def __init__(self, token: str | None = None, org: str | None = None,
                 api_url: str = "https://api.github.com", timeout: int = 20):
        self.token = (token or "").strip()
        self.org = (org or "").strip()
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.ultima_llamada_ok = None

    # -- interno ----------------------------------------------------------
    def _headers(self) -> dict:
        cabeceras = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
        }
        if self.token:
            cabeceras["Authorization"] = f"Bearer {self.token}"
        return cabeceras

    def _get(self, ruta: str, params: dict | None = None) -> tuple[object, dict]:
        url = ruta if ruta.startswith("http") else f"{self.api_url}{ruta}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        peticion = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as resp:
                cuerpo = json.loads(resp.read().decode("utf-8"))
                self.ultima_llamada_ok = datetime.now(timezone.utc)
                return cuerpo, dict(resp.headers)
        except urllib.error.HTTPError as err:
            cabeceras = dict(err.headers or {})
            restantes = cabeceras.get("X-RateLimit-Remaining")
            if err.code in (403, 429) and restantes == "0":
                reset = cabeceras.get("X-RateLimit-Reset")
                raise RateLimitError(
                    f"Límite de la GitHub API excedido (HTTP {err.code}).",
                    int(reset) if reset else None,
                ) from err
            raise GitHubError(f"HTTP {err.code} al consultar {url}") from err
        except urllib.error.URLError as err:
            raise GitHubError(f"Error de red al consultar {url}: {err.reason}") from err

    def _paginado(self, ruta: str, params: dict | None = None, max_paginas: int = 10) -> list:
        """Recorre las páginas siguiendo la cabecera Link."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        resultados: list = []
        siguiente = ruta
        primera = True
        for _ in range(max_paginas):
            datos, cabeceras = self._get(siguiente, params if primera else None)
            primera = False
            if not isinstance(datos, list):
                return datos
            resultados.extend(datos)
            siguiente = self._siguiente_enlace(cabeceras.get("Link", ""))
            if not siguiente:
                break
        return resultados

    @staticmethod
    def _siguiente_enlace(cabecera_link: str) -> str | None:
        for parte in cabecera_link.split(","):
            seccion = parte.split(";")
            if len(seccion) == 2 and 'rel="next"' in seccion[1]:
                return seccion[0].strip().strip("<>")
        return None

    # -- endpoints públicos ----------------------------------------------
    def rate_limit(self) -> dict:
        """GET /rate_limit — se consulta antes de cada corrida."""
        datos, _ = self._get("/rate_limit")
        nucleo = datos.get("resources", {}).get("core", {})
        return {
            "limite": nucleo.get("limit"),
            "restantes": nucleo.get("remaining"),
            "reset": nucleo.get("reset"),
            "autenticado": bool(self.token),
        }

    def _repo_ruta(self, repo: str) -> str:
        """Acepta 'owner/repo' o solo 'repo' (usa GITHUB_ORG)."""
        if "/" in repo:
            return f"/repos/{repo}"
        if not self.org:
            raise GitHubError(f"Falta GITHUB_ORG para resolver el repositorio '{repo}'.")
        return f"/repos/{self.org}/{repo}"

    def commits(self, repo: str, desde: str | None = None) -> list[dict]:
        """GET /repos/{org}/{repo}/commits — normaliza autor, fecha y mensaje."""
        params = {}
        if desde:
            params["since"] = desde
        crudos = self._paginado(f"{self._repo_ruta(repo)}/commits", params)
        salida = []
        for item in crudos:
            commit = item.get("commit", {})
            autor_api = item.get("author") or {}
            autor_git = commit.get("author", {}) or {}
            salida.append({
                "sha": (item.get("sha") or "")[:7],
                "mensaje": (commit.get("message") or "").split("\n")[0],
                "autor": autor_api.get("login") or autor_git.get("name") or "desconocido",
                "fecha": autor_git.get("date"),
            })
        return salida

    def branches(self, repo: str) -> list[str]:
        """GET /repos/{org}/{repo}/branches"""
        return [b.get("name") for b in self._paginado(f"{self._repo_ruta(repo)}/branches")]

    def pull_requests(self, repo: str, estado: str = "all") -> list[dict]:
        """GET /repos/{org}/{repo}/pulls?state=all"""
        crudos = self._paginado(f"{self._repo_ruta(repo)}/pulls", {"state": estado})
        return [{
            "numero": pr.get("number"),
            "titulo": pr.get("title"),
            "autor": (pr.get("user") or {}).get("login", "desconocido"),
            "estado": pr.get("state"),
            "fecha": pr.get("created_at"),
            "rama": (pr.get("head") or {}).get("ref"),
        } for pr in crudos]

    def issues(self, repo: str, estado: str = "all") -> list[dict]:
        """GET /repos/{org}/{repo}/issues?state=all (excluye PRs)."""
        crudos = self._paginado(f"{self._repo_ruta(repo)}/issues", {"state": estado})
        return [{
            "numero": it.get("number"),
            "titulo": it.get("title"),
            "autor": (it.get("user") or {}).get("login", "desconocido"),
            "estado": it.get("state"),
            "fecha": it.get("created_at"),
        } for it in crudos if "pull_request" not in it]

    def actividad_repo(self, repo: str, desde: str | None = None) -> dict:
        """Todo lo que HU-001 necesita de un repositorio, en una sola llamada."""
        return {
            "repositorio": repo,
            "consultado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "commits": self.commits(repo, desde),
            "ramas": self.branches(repo),
            "pull_requests": self.pull_requests(repo),
            "issues": self.issues(repo),
        }
