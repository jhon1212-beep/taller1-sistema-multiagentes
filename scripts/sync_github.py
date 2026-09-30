# -*- coding: utf-8 -*-
"""
HU-001 / HU-004 · Agente recolector de GitHub
Sincroniza los repositorios de los equipos y calcula los indicadores
del proyecto. Escribe JSON en data/ para que el panel los consuma.

Uso:
    python scripts/sync_github.py                # todos los equipos
    python scripts/sync_github.py --equipo Beta  # uno solo
    python scripts/sync_github.py --check        # solo prueba la conexión

Si la API falla o excede su límite, se conservan los datos de la última
sincronización y la fuente se marca como "degradada" (criterio de HU-001).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from github_client import GitHubClient, GitHubError, RateLimitError, cargar_env  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_CONFIG = os.path.join(RAIZ, "config")
DIR_DATOS = os.path.join(RAIZ, "data")


def log(etiqueta: str, mensaje: str) -> None:
    print(f"[{etiqueta}] {mensaje}")


# --------------------------------------------------------------------------
# Indicadores
# --------------------------------------------------------------------------
def gini(valores: list[int]) -> float:
    """Coeficiente de Gini sobre la distribución de commits por integrante."""
    n = len(valores)
    if n == 0:
        return 0.0
    total = sum(valores)
    if total == 0:
        return 0.0
    orden = sorted(valores)
    acumulado = sum((i + 1) * v for i, v in enumerate(orden))
    return round((2 * acumulado) / (n * total) - (n + 1) / n, 3)


def gini_normalizado(valores: list[int]) -> float:
    """Gini dividido por su máximo teórico para ese tamaño de equipo.

    Para n integrantes el máximo alcanzable es (n-1)/n, no 1. Sin normalizar,
    un equipo de 3 nunca podría superar 0.667 y la comparación entre equipos
    de distinto tamaño sería injusta.
    """
    n = len(valores)
    if n < 2:
        return 0.0
    maximo = (n - 1) / n
    return round(min(1.0, gini(valores) / maximo), 3)


def metricas(commits: list[dict], deadline: str | None, dias_ventana: int = 42) -> dict:
    """Ritmo, regularidad y equidad contributiva a partir de los commits."""
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=dias_ventana)

    por_autor: dict[str, int] = {}
    dias_activos: set[str] = set()
    recientes = 0

    limite_48h = None
    if deadline:
        try:
            fecha_limite = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            limite_48h = fecha_limite - timedelta(hours=48)
        except ValueError:
            limite_48h = None

    en_ventana = 0
    for commit in commits:
        if not commit.get("fecha"):
            continue
        try:
            fecha = datetime.fromisoformat(commit["fecha"].replace("Z", "+00:00"))
        except ValueError:
            continue
        por_autor[commit["autor"]] = por_autor.get(commit["autor"], 0) + 1
        if fecha >= desde:
            en_ventana += 1
            dias_activos.add(fecha.date().isoformat())
        if limite_48h and limite_48h <= fecha <= fecha_limite:
            recientes += 1

    reparto = list(por_autor.values())
    return {
        "commits_total": len(commits),
        "commits_en_ventana": en_ventana,
        "commits_por_autor": dict(sorted(por_autor.items(), key=lambda x: -x[1])),
        "dias_con_commit": len(dias_activos),
        "dias_ventana": dias_ventana,
        "pct_commits_48h_previas": (
            round(100 * recientes / en_ventana, 1) if (limite_48h and en_ventana) else None
        ),
        "gini": gini(reparto),
        "gini_normalizado": gini_normalizado(reparto),
        "integrantes_detectados": len(reparto),
    }


# --------------------------------------------------------------------------
# Utilidades de archivo
# --------------------------------------------------------------------------
def leer_json(ruta: str, por_defecto=None):
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return por_defecto
    return por_defecto


def escribir_json(ruta: str, datos) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# Sincronización
# --------------------------------------------------------------------------
def sincronizar(cliente: GitHubClient, equipos: list[dict], filtro: str | None = None) -> dict:
    resumen = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente": "github",
        "equipos": [],
        "incidencias": [],
    }

    for equipo in equipos:
        nombre = equipo.get("nombre", "sin-nombre")
        if filtro and filtro.lower() not in nombre.lower():
            continue
        repo = equipo.get("repositorio")
        archivo = os.path.join(DIR_DATOS, f"github_{nombre.lower().replace(' ', '_')}.json")

        try:
            actividad = cliente.actividad_repo(repo)
            actividad["equipo"] = nombre
            actividad["metricas"] = metricas(actividad["commits"], equipo.get("deadline_sprint"))
            actividad["estado_fuente"] = "ok"
            escribir_json(archivo, actividad)
            log("recolector", f"{nombre}: {len(actividad['commits'])} commits, "
                             f"{len(actividad['pull_requests'])} PR, {len(actividad['issues'])} issues")

        except RateLimitError as err:
            previo = leer_json(archivo)
            log("recolector", f"⚠ {nombre}: {err} Reintento en {err.segundos_para_reset}s. "
                              f"Se usan los datos de la última sincronización.")
            resumen["incidencias"].append({
                "equipo": nombre, "tipo": "rate_limit", "detalle": str(err),
                "reintento_en_segundos": err.segundos_para_reset,
            })
            if previo:
                previo["estado_fuente"] = "degradada"
                escribir_json(archivo, previo)
                actividad = previo
            else:
                continue

        except GitHubError as err:
            previo = leer_json(archivo)
            log("recolector", f"⚠ {nombre}: {err} Se conserva la última sincronización.")
            resumen["incidencias"].append({"equipo": nombre, "tipo": "error_api", "detalle": str(err)})
            if previo:
                previo["estado_fuente"] = "degradada"
                escribir_json(archivo, previo)
                actividad = previo
            else:
                continue

        resumen["equipos"].append({
            "equipo": nombre,
            "repositorio": repo,
            "estado_fuente": actividad.get("estado_fuente", "ok"),
            "consultado": actividad.get("consultado"),
            "metricas": actividad.get("metricas", {}),
        })

    escribir_json(os.path.join(DIR_DATOS, "resumen_github.json"), resumen)
    return resumen


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente recolector de GitHub (HU-001).")
    parser.add_argument("--equipo", help="sincronizar solo el equipo indicado")
    parser.add_argument("--check", action="store_true", help="solo probar la conexión y el rate limit")
    parser.add_argument("--config", default="equipos.json",
                        help="archivo de config/ a usar (por defecto equipos.json; "
                             "usa equipos.ejemplo.json para la prueba de humo)")
    args = parser.parse_args()

    env = cargar_env()
    token = env.get("GITHUB_TOKEN", "")
    org = env.get("GITHUB_ORG", "")
    api = env.get("GITHUB_API_URL", "https://api.github.com")

    if not token or token.startswith("ghp_xxxx"):
        log("config", "⚠ No hay GITHUB_TOKEN válido en .env — se usará acceso anónimo "
                      "(60 peticiones/hora y solo repositorios públicos).")

    cliente = GitHubClient(token=token, org=org, api_url=api)

    try:
        limite = cliente.rate_limit()
        log("config", f"Conexión OK · autenticado={limite['autenticado']} · "
                      f"peticiones restantes={limite['restantes']}/{limite['limite']}")
    except GitHubError as err:
        log("config", f"✖ No se pudo contactar la GitHub API: {err}")
        return 1

    if args.check:
        return 0

    ruta_config = os.path.join(DIR_CONFIG, args.config)
    equipos = leer_json(ruta_config, {}).get("equipos", [])
    if not equipos:
        log("config", f"✖ No hay equipos en config/{args.config}")
        return 1

    resumen = sincronizar(cliente, equipos, args.equipo)
    log("recolector", f"Sincronización terminada: {len(resumen['equipos'])} equipo(s), "
                      f"{len(resumen['incidencias'])} incidencia(s).")
    log("recolector", f"Salida: {os.path.join(DIR_DATOS, 'resumen_github.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
