# -*- coding: utf-8 -*-
"""Pruebas de carga y disponibilidad de la API (atributos de calidad: rendimiento y disponibilidad).

Escenarios, uno por tipo de usuario:
  - VisitanteAnonimo : /health y rutas protegidas sin token (debe responder 401, nunca 5xx).
  - DocenteEnSesion  : login una vez y luego consulta proyectos y tareas, como el frontend.

Variables de entorno (nada de credenciales en el repositorio):
  CARGA_CORREO, CARGA_PASSWORD   docente de pruebas ya existente en la base objetivo.
  CARGA_PROYECTO_ID              proyecto a consultar (opcional; si falta se toma el primero del listado).
  CARGA_P95_MS                   umbral de p95 en ms (por defecto 1500).
  CARGA_MAX_FALLOS_PCT           porcentaje maximo de fallos (por defecto 1).

El proceso termina con codigo 1 si se superan los umbrales, para que la CI lo marque en rojo.
"""
from __future__ import annotations

import os
import random

from locust import HttpUser, between, events, task

CORREO = os.getenv("CARGA_CORREO", "")
PASSWORD = os.getenv("CARGA_PASSWORD", "")
PROYECTO_ID = os.getenv("CARGA_PROYECTO_ID", "")
UMBRAL_P95_MS = float(os.getenv("CARGA_P95_MS", "1500"))
UMBRAL_FALLOS_PCT = float(os.getenv("CARGA_MAX_FALLOS_PCT", "1"))


class VisitanteAnonimo(HttpUser):
    """Trafico sin sesion: sondeos de salud y accesos no autorizados."""

    weight = 1
    wait_time = between(0.5, 2)

    @task(5)
    def salud(self):
        self.client.get("/health", name="GET /health")

    @task(1)
    def perfil_sin_token(self):
        # Un 401 es la respuesta correcta; solo un 5xx cuenta como fallo.
        with self.client.get("/auth/me", name="GET /auth/me (sin token)", catch_response=True) as r:
            if r.status_code == 401:
                r.success()
            else:
                r.failure(f"se esperaba 401 y llego {r.status_code}")


class DocenteEnSesion(HttpUser):
    """Docente autenticado que navega por proyectos y tareas."""

    weight = 4
    wait_time = between(1, 3)

    def on_start(self):
        self.cabeceras = {}
        self.proyecto_id = PROYECTO_ID or None
        if not CORREO or not PASSWORD:
            # Sin credenciales no hay sesion: el usuario solo hace /health.
            return
        with self.client.post(
            "/auth/login",
            json={"correo": CORREO, "password": PASSWORD},
            name="POST /auth/login",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                self.cabeceras = {"Authorization": f"Bearer {r.json()['token']}"}
            else:
                r.failure(f"login fallido: {r.status_code}")
        if self.cabeceras and not self.proyecto_id:
            self._elegir_proyecto()

    def _elegir_proyecto(self):
        r = self.client.get("/proyectos", headers=self.cabeceras, name="GET /proyectos")
        if r.status_code == 200 and r.json():
            self.proyecto_id = r.json()[0]["id"]

    @task(3)
    def listar_proyectos(self):
        if self.cabeceras:
            self.client.get("/proyectos", headers=self.cabeceras, name="GET /proyectos")

    @task(3)
    def ver_proyecto(self):
        if self.cabeceras and self.proyecto_id:
            self.client.get(
                f"/proyectos/{self.proyecto_id}", headers=self.cabeceras, name="GET /proyectos/{id}"
            )

    @task(2)
    def tareas_del_proyecto(self):
        if self.cabeceras and self.proyecto_id:
            self.client.get(
                f"/proyectos/{self.proyecto_id}/tareas?limite={random.choice([20, 50, 100])}",
                headers=self.cabeceras,
                name="GET /proyectos/{id}/tareas",
            )

    @task(1)
    def perfil(self):
        if self.cabeceras:
            self.client.get("/auth/me", headers=self.cabeceras, name="GET /auth/me")


@events.quitting.add_listener
def validar_umbrales(environment, **_):
    total = environment.stats.total
    if total.num_requests == 0:
        environment.process_exit_code = 1
        return
    fallos_pct = 100 * total.num_failures / total.num_requests
    p95 = total.get_response_time_percentile(0.95) or 0
    if fallos_pct > UMBRAL_FALLOS_PCT or p95 > UMBRAL_P95_MS:
        print(
            f"UMBRALES SUPERADOS: fallos {fallos_pct:.2f}% (max {UMBRAL_FALLOS_PCT}%), "
            f"p95 {p95:.0f} ms (max {UMBRAL_P95_MS:.0f} ms)"
        )
        environment.process_exit_code = 1
    else:
        print(f"UMBRALES OK: fallos {fallos_pct:.2f}%, p95 {p95:.0f} ms")
