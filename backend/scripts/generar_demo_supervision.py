# -*- coding: utf-8 -*-
"""HU-006 / HU-007 · Genera los datos de supervisión que muestra el frontend.

Calcula con el motor real (TA-019) los indicadores I1–I4 y las alertas R1–R4 de
cada proyecto del dataset de TA-017, y añade la explicación de la plantilla
(AR-02) y la evidencia de origen de cada alerta. El resultado se escribe en
frontend/src/datos/demo_supervision.js, que el frontend usa mientras el
dashboard no consume la API (TA-040).

    python backend/scripts/generar_demo_supervision.py

No editar el archivo generado a mano: tests/unit/test_demo_supervision_frontend.py
comprueba que coincide con esta salida.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402
from app.modulos.supervision.adaptadores.plantilla import (  # noqa: E402
    DESCRIPCIONES,
    GeneradorExplicacionPlantilla,
)
from app.modulos.supervision.motor_indicadores import evaluar, parsear_fecha  # noqa: E402

SALIDA = RAIZ / "frontend" / "src" / "datos" / "demo_supervision.js"


def _evidencia_de_origen(alerta: dict, por_id: dict[str, dict]) -> dict:
    """Describe, para la pantalla de detalle, el registro que originó la alerta."""
    ev = por_id.get(alerta["evidencia_ids"][0]) if alerta["evidencia_ids"] else None
    if ev is None:
        return {}
    comun = {"id": ev["id_externo"], "responsable": ev["autor"], "fecha": ev["fecha"]}
    if ev["fuente"] == "notion":
        return {**comun, "tipo": "tarea", "titulo": ev["descripcion"], "estado": ev["estado"],
                "fecha_limite": ev["fecha_limite"]}
    if ev["fuente"] == "github":
        return {**comun, "tipo": "commit", "titulo": ev["descripcion"], "sha": ev["id_externo"][:7]}
    return {**comun, "tipo": "documento", "titulo": ev["descripcion"], "tipo_archivo": ev.get("tipo_archivo")}


def _detalle(evidencias: list[dict], corte: str) -> dict:
    """Cifras que explican cada indicador (se muestran en el tooltip)."""
    tareas = [e for e in evidencias if e["fuente"] == "notion"]
    fecha_corte = parsear_fecha(corte)
    fechas = [parsear_fecha(e["fecha"]) for e in evidencias]
    ultima = max(f for f in fechas if f is not None and f <= fecha_corte)
    return {
        "tareas_total": len(tareas),
        "tareas_listas": sum(1 for t in tareas if t["estado"] == "Listo"),
        "ultima_actividad": ultima.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidencias": {f: sum(1 for e in evidencias if e["fuente"] == f) for f in ("github", "notion", "drive")},
    }


def construir() -> dict:
    datos = cargar_dataset()
    corte = datos["fecha_corte"]
    explicador = GeneradorExplicacionPlantilla()
    proyectos = {}
    for proyecto in datos["proyectos"]:
        pid = proyecto["id"]
        evidencias = [e for e in datos["evidencias"] if e["proyecto_id"] == pid]
        por_id = {e["id_externo"]: e for e in evidencias}
        resultado = evaluar(evidencias, corte)
        alertas = []
        for numero, a in enumerate(resultado["alertas"], start=1):
            explicacion = explicador.generar(a, corte)
            alertas.append({
                "id": f"{a['regla']}-{a['evidencia_ids'][0][:12]}",
                "regla": a["regla"],
                "fuente": a["fuente"],
                "evidencia_ids": a["evidencia_ids"],
                "explicacion": explicacion["texto"],
                "origen_explicacion": explicacion["origen"],
                "evidencia": _evidencia_de_origen(a, por_id),
            })
        proyectos[pid] = {
            "nombre": proyecto["nombre"],
            "indicadores": resultado["indicadores"],
            "detalle": _detalle(evidencias, corte),
            "alertas": alertas,
        }
    return {"fecha_corte": corte, "reglas": DESCRIPCIONES, "proyectos": proyectos}


def a_js(datos: dict) -> str:
    cuerpo = json.dumps(datos["proyectos"], ensure_ascii=False, indent=2)
    reglas = json.dumps(datos["reglas"], ensure_ascii=False, indent=2)
    return (
        "/**\n"
        " * HU-006 / HU-007 · Datos de supervisión (indicadores I1–I4 y alertas R1–R4).\n"
        " * Generado por backend/scripts/generar_demo_supervision.py con el motor de TA-019\n"
        " * sobre el dataset de TA-017; no editar a mano. Se reemplaza por la API en TA-040.\n"
        " */\n\n"
        f"export const FECHA_CORTE = {json.dumps(datos['fecha_corte'])}\n\n"
        f"export const DESCRIPCION_REGLAS = {reglas}\n\n"
        f"export const SUPERVISION_DEMO = {cuerpo}\n"
    )


if __name__ == "__main__":
    SALIDA.write_text(a_js(construir()), encoding="utf-8", newline="\n")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
    for pid, p in construir()["proyectos"].items():
        print(f"  proyecto {pid}: {p['indicadores']} · {len(p['alertas'])} alertas "
              f"({', '.join(sorted({a['regla'] for a in p['alertas']}))})")
