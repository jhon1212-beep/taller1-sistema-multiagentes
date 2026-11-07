"""TA-022 / TA-033: ejecuta el corte diario llamando a la ruta de consolidación.

Lo usa .github/workflows/corte.yml. Pasos:
1. Espera a que la API responda en /health (el arranque puede tardar).
2. Inicia sesión con el docente del corte (HU-001) para obtener el JWT.
3. Lista los proyectos del docente y, por cada proyecto activo, llama a
   POST /proyectos/{id}/consolidacion (TA-022), que corre el grafo de agentes
   y guarda el corte en PostgreSQL (TA-018).
4. Imprime un resumen en JSON. Termina con código 1 si algún proyecto falló.

Variables de entorno:
    API_URL       URL de la API (por defecto http://localhost:8000)
    CORTE_CORREO  correo del docente con el que se ejecuta el corte
    CORTE_CLAVE   su contraseña (en GitHub va como Repository secret)
    CORTE_FECHA   opcional: fecha de corte ISO 8601 con zona; vacío = fin del día en Lima

Uso local:
    python backend/scripts/ejecutar_corte.py
"""
from __future__ import annotations

import json
import os
import sys
import time

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
ESPERA_MAXIMA_S = 90
TIMEOUT_S = 120  # la consolidación consulta GitHub, Notion y Drive


def esperar_api() -> None:
    limite = time.monotonic() + ESPERA_MAXIMA_S
    while time.monotonic() < limite:
        try:
            if requests.get(f"{API_URL}/health", timeout=5).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    sys.exit(f"La API no respondió en {ESPERA_MAXIMA_S} s: {API_URL}/health")


def iniciar_sesion() -> dict[str, str]:
    correo, clave = os.getenv("CORTE_CORREO", ""), os.getenv("CORTE_CLAVE", "")
    if not correo or not clave:
        sys.exit("Faltan CORTE_CORREO y CORTE_CLAVE.")
    respuesta = requests.post(
        f"{API_URL}/auth/login", json={"correo": correo, "password": clave}, timeout=30
    )
    if respuesta.status_code != 200:
        sys.exit(f"Inicio de sesión rechazado ({respuesta.status_code}).")
    return {"Authorization": f"Bearer {respuesta.json()['token']}"}


def main() -> int:
    esperar_api()
    cabeceras = iniciar_sesion()
    proyectos = requests.get(f"{API_URL}/proyectos", headers=cabeceras, timeout=30)
    proyectos.raise_for_status()

    cuerpo = {"fecha_corte": os.environ["CORTE_FECHA"]} if os.getenv("CORTE_FECHA") else {}
    resumen, fallos = [], 0
    for proyecto in (p for p in proyectos.json() if p.get("activo")):
        inicio = time.perf_counter()
        r = requests.post(
            f"{API_URL}/proyectos/{proyecto['id']}/consolidacion",
            json=cuerpo, headers=cabeceras, timeout=TIMEOUT_S,
        )
        fila = {
            "proyecto_id": proyecto["id"],
            "http": r.status_code,
            "segundos": round(time.perf_counter() - inicio, 2),
        }
        if r.status_code == 200:
            datos = r.json()
            fila.update({
                "fecha_corte": datos["fecha_corte"],
                "fuentes": {f: v["estado"] for f, v in datos["fuentes"].items()},
                "indicadores": datos["indicadores"],
                "alertas": len(datos["alertas"]),
            })
        else:
            fallos += 1
            fila["detalle"] = r.text[:300]
        resumen.append(fila)

    print(json.dumps({"proyectos": len(resumen), "fallos": fallos, "cortes": resumen},
                     ensure_ascii=False, indent=2))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
