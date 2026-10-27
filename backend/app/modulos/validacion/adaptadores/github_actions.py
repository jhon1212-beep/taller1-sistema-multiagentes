# -*- coding: utf-8 -*-
"""TA-021 · EjecutorE2EGitHubActions: ejecutor real del puerto EjecutorE2E.

Flujo (los pasos que pide la estimación de TA-021):

1. Disparo por API: POST .../actions/workflows/{workflow}/dispatches con los
   parámetros del workflow TA-047 (url_publica, elemento_verificar, proyecto_id) y un
   código de correlación. GitHub responde 204 sin id de ejecución.
2. Localizar el run: el workflow se llama «E2E <correlacion> - proyecto <id>»; se
   busca entre las últimas ejecuciones de workflow_dispatch la que lleva ese código.
3. Recepción del resultado: se consulta el run hasta que termine. conclusion
   «success» → PASS, «failure» → FAIL (resultado funcional, no excepción). Cualquier otra
   cosa (cancelado, tiempo agotado, no apareció el run) lanza
   ErrorInfraestructuraValidacion.

El transporte HTTP es inyectable para probar sin red (tests/unit).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from app.modulos.validacion.dominio import (
    ErrorInfraestructuraValidacion,
    ResultadoValidacion,
    SolicitudValidacion,
)

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"

# (metodo, url, cuerpo | None) -> (codigo_http, json | None)
Transporte = Callable[[str, str, dict | None], tuple[int, Any]]


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


class EjecutorE2EGitHubActions:
    def __init__(
        self,
        *,
        repositorio: str,
        token: str,
        workflow: str = "e2e.yml",
        ref: str = "main",
        api_url: str = API_URL,
        transporte: Transporte | None = None,
        espera: Callable[[float], None] = time.sleep,
        tiempo_max_s: float = 300,
        intervalo_s: float = 5,
        intentos_localizar: int = 6,
    ) -> None:
        if not repositorio or not token:
            raise ErrorInfraestructuraValidacion("Faltan el repositorio y/o el token de GitHub.")
        self._repo = repositorio
        self._token = token
        self._workflow = workflow
        self._ref = ref
        self._api = api_url.rstrip("/")
        self._transporte = transporte or self._http
        self._espera = espera
        self._tiempo_max_s = tiempo_max_s
        self._intervalo_s = intervalo_s
        self._intentos_localizar = intentos_localizar

    # -- HTTP real ----------------------------------------------------------
    def _http(self, metodo: str, url: str, cuerpo: dict | None) -> tuple[int, Any]:
        peticion = urllib.request.Request(
            url,
            method=metodo,
            data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "agente-validacion/1.0",
            },
        )
        try:
            with urllib.request.urlopen(peticion, timeout=30) as r:
                bruto = r.read()
                return r.status, (json.loads(bruto) if bruto else None)
        except urllib.error.HTTPError as e:
            return e.code, None
        except (urllib.error.URLError, TimeoutError) as e:
            raise ErrorInfraestructuraValidacion(f"No se pudo contactar a GitHub: {e}") from e

    def _llamar(self, metodo: str, ruta: str, cuerpo: dict | None = None) -> tuple[int, Any]:
        return self._transporte(metodo, f"{self._api}/repos/{self._repo}{ruta}", cuerpo)

    # -- pasos --------------------------------------------------------------
    def _disparar(self, s: SolicitudValidacion, correlacion: str) -> None:
        codigo, _ = self._llamar(
            "POST",
            f"/actions/workflows/{self._workflow}/dispatches",
            {
                "ref": self._ref,
                "inputs": {
                    "url_publica": s.url_publica,
                    "elemento_verificar": s.elemento_verificar,
                    "proyecto_id": str(s.proyecto_id),
                    "correlacion": correlacion,
                },
            },
        )
        if codigo != 204:
            raise ErrorInfraestructuraValidacion(
                f"GitHub rechazó el disparo del workflow (HTTP {codigo})."
            )

    def _localizar(self, correlacion: str) -> dict:
        ruta = f"/actions/workflows/{self._workflow}/runs?event=workflow_dispatch&per_page=20"
        for intento in range(self._intentos_localizar):
            codigo, datos = self._llamar("GET", ruta)
            if codigo == 200:
                for run in datos.get("workflow_runs", []):
                    if correlacion in (run.get("name") or run.get("display_title") or ""):
                        return run
            if intento < self._intentos_localizar - 1:
                self._espera(self._intervalo_s)
        raise ErrorInfraestructuraValidacion("No apareció la ejecución del workflow en GitHub.")

    def _esperar(self, run_id: int) -> dict:
        esperado = 0.0
        while True:
            codigo, run = self._llamar("GET", f"/actions/runs/{run_id}")
            if codigo == 200 and run.get("status") == "completed":
                return run
            if esperado >= self._tiempo_max_s:
                raise ErrorInfraestructuraValidacion(
                    f"El run {run_id} no terminó en {self._tiempo_max_s:.0f} s."
                )
            self._espera(self._intervalo_s)
            esperado += self._intervalo_s

    @staticmethod
    def _a_resultado(run: dict, s: SolicitudValidacion) -> ResultadoValidacion:
        conclusion = run.get("conclusion")
        if conclusion not in ("success", "failure"):
            raise ErrorInfraestructuraValidacion(
                f"El run {run['id']} terminó en «{conclusion}», sin PASS ni FAIL."
            )
        inicio = _fecha(run.get("run_started_at") or run["created_at"])
        fin = _fecha(run["updated_at"])
        es_pass = conclusion == "success"
        return ResultadoValidacion(
            proyecto_id=s.proyecto_id,
            resultado="PASS" if es_pass else "FAIL",
            duracion_ms=max(0, int((fin - inicio).total_seconds() * 1000)),
            ejecutada_en=fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc),
            run_id_actions=int(run["id"]),
            captura_url=None if es_pass else f"{run['html_url']}#artifacts",
        )

    # -- puerto EjecutorE2E -------------------------------------------------
    def ejecutar(self, solicitud: SolicitudValidacion) -> ResultadoValidacion:
        correlacion = uuid.uuid4().hex[:12]
        self._disparar(solicitud, correlacion)
        run = self._localizar(correlacion)
        run = self._esperar(int(run["id"]))
        return self._a_resultado(run, solicitud)
