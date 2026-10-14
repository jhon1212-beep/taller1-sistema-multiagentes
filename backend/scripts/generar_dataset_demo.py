# -*- coding: utf-8 -*-
"""TA-017 · Genera el dataset controlado del proyecto demo.

Es determinista (sin azar ni reloj): ejecutarlo dos veces produce el mismo
JSON. Escribe backend/app/modulos/evidencias/dataset/proyecto_demo.json.

    python backend/scripts/generar_dataset_demo.py

Dos proyectos, pensados para ejercitar las reglas de alerta:
  1 "Seguimiento académico": activo; dispara R1 y R2 (Notion), no R3 ni R4.
  2 "Biblioteca digital":    estancado; dispara R3 (GitHub) y R4 (Drive), además de R1 y R2.
Los indicadores y alertas esperados los calcula el motor real de TA-019
(app.modulos.supervision.motor) y quedan en el JSON; las pruebas del motor
los contrastan con valores calculados a mano.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modulos.evidencias.dataset import _a_evidencia  # noqa: E402
from app.modulos.supervision.motor import evaluar  # noqa: E402

FECHA_CORTE = datetime(2026, 10, 13, 4, 59, 59, tzinfo=timezone.utc)  # 12/10 23:59 -05:00
SALIDA = (
    Path(__file__).resolve().parents[1]
    / "app" / "modulos" / "evidencias" / "dataset" / "proyecto_demo.json"
)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(semilla: str) -> str:
    return hashlib.sha1(semilla.encode()).hexdigest()


def d(texto: str) -> datetime:
    return datetime.fromisoformat(texto).replace(tzinfo=timezone.utc)


# --- Proyecto 1 -----------------------------------------------------------
EQUIPO_1 = ["Ana Torres", "Luis Vega", "Marta Ruiz", "Diego Paz"]
MENSAJES = [
    "Agregar validación del formulario",
    "Mostrar tareas por proyecto",
    "Corregir filtro de fechas",
    "Documentar ejecución de pruebas",
    "Añadir estados de integración",
]
TITULOS = [
    "Inicio de sesión docente",
    "Registro de proyecto",
    "Listado de commits",
    "Consulta de tareas",
    "Pruebas de integración",
]
DOCS = ["Plan del proyecto", "Arquitectura", "Plan de pruebas", "Informe de avance", "Diseño de interfaz"]


def commits(pid: int, equipo: list[str], n: int, inicio: str, paso_h: int) -> list[dict]:
    base = d(inicio)
    return [
        {
            "fuente": "github",
            "id_externo": sha(f"commit-{pid}-{i}"),
            "autor": equipo[i % len(equipo)],
            "fecha": iso(base + timedelta(hours=paso_h * i)),
            "descripcion": MENSAJES[i % 5],
            "proyecto_id": pid,
        }
        for i in range(n)
    ]


def documentos(pid: int, equipo: list[str], n: int, inicio: str, paso_d: int) -> list[dict]:
    base = d(inicio)
    return [
        {
            "fuente": "drive",
            "id_externo": f"archivo-p{pid}-{i + 1:02d}",
            "autor": equipo[i % len(equipo)],
            "fecha": iso(base + timedelta(days=paso_d * i)),
            "descripcion": f"{DOCS[i % 5]} · {i + 1}",
            "proyecto_id": pid,
            "tipo_archivo": "application/pdf" if i % 2 == 0 else "application/vnd.google-apps.document",
        }
        for i in range(n)
    ]


def tarea(pid, n, titulo, autor, estado, editada, limite) -> dict:
    return {
        "fuente": "notion",
        "id_externo": f"tarea-p{pid}-{n:02d}",
        "autor": autor,
        "fecha": editada,
        "descripcion": titulo,
        "proyecto_id": pid,
        "estado": estado,
        "fecha_limite": limite,
    }


def tareas_p1() -> list[dict]:
    # (estado, última edición, fecha límite). Casos de regla marcados.
    filas = [
        ("Listo", "2026-10-01T15:00:00Z", "2026-10-05"),
        ("Listo", "2026-10-02T15:00:00Z", "2026-10-06"),
        ("Listo", "2026-10-03T15:00:00Z", "2026-10-07"),
        ("Listo", "2026-10-04T15:00:00Z", "2026-10-08"),
        ("Listo", "2026-10-05T15:00:00Z", "2026-10-09"),
        ("Listo", "2026-10-06T15:00:00Z", "2026-10-10"),
        ("Listo", "2026-10-07T15:00:00Z", "2026-10-11"),
        ("Listo", "2026-10-08T15:00:00Z", "2026-10-11"),
        ("En curso", "2026-10-02T15:00:00Z", "2026-10-07"),  # R1 y R2
        ("En curso", "2026-10-03T15:00:00Z", "2026-10-20"),  # R2
        ("En curso", "2026-10-09T15:00:00Z", "2026-10-20"),
        ("En curso", "2026-10-10T15:00:00Z", "2026-10-09"),  # R1
        ("En curso", "2026-10-11T15:00:00Z", "2026-10-21"),
        ("En curso", "2026-10-12T09:00:00Z", "2026-10-22"),
        ("Sin empezar", "2026-09-28T15:00:00Z", "2026-10-08"),  # R1
        ("Sin empezar", "2026-09-29T15:00:00Z", "2026-10-10"),  # R1
        ("Sin empezar", "2026-10-05T15:00:00Z", "2026-10-25"),
        ("Sin empezar", "2026-10-06T15:00:00Z", "2026-10-26"),
        ("Sin empezar", "2026-10-07T15:00:00Z", "2026-10-27"),
        ("Sin empezar", "2026-10-08T15:00:00Z", "2026-10-28"),
    ]
    salida = []
    for i, (estado, editada, limite) in enumerate(filas):
        autor = None if i == 19 else EQUIPO_1[i % 4]  # la última no tiene responsable
        salida.append(tarea(1, i + 1, f"{TITULOS[i % 5]} · {i + 1}", autor, estado, editada, limite))
    return salida


def tareas_p2() -> list[dict]:
    equipo = ["Elena Ríos", "Carlos León"]
    filas = [
        ("Listo", "2026-09-24T15:00:00Z", "2026-09-30"),
        ("Listo", "2026-09-25T15:00:00Z", "2026-10-01"),
        ("Listo", "2026-09-26T15:00:00Z", "2026-10-02"),
        ("En curso", "2026-09-27T15:00:00Z", "2026-10-04"),  # R1 y R2
        ("En curso", "2026-09-28T15:00:00Z", "2026-10-30"),  # R2
        ("En curso", "2026-10-02T15:00:00Z", "2026-10-31"),  # R2
        ("Sin empezar", "2026-09-26T15:00:00Z", "2026-10-03"),  # R1
        ("Sin empezar", "2026-09-27T15:00:00Z", "2026-11-05"),
    ]
    return [
        tarea(2, i + 1, f"Módulo de catálogo · {i + 1}", equipo[i % 2], e, f, l)
        for i, (e, f, l) in enumerate(filas)
    ]


def evaluar_con_motor(evidencias: list[dict], pid: int) -> tuple[dict, list[dict]]:
    """Indicadores y alertas calculados por el motor real (TA-019)."""
    mias = [_a_evidencia(e) for e in evidencias if e["proyecto_id"] == pid]
    indicadores, alertas = evaluar(mias, iso(FECHA_CORTE))
    return indicadores, [
        {"regla": a["regla"], "fuente": a["fuente"], "evidencia_id": a["evidencia_ids"][0]}
        for a in alertas
    ]


def construir() -> dict:
    evidencias = (
        commits(1, EQUIPO_1, 20, "2026-09-22T14:00:00", 25)
        + tareas_p1()
        + documentos(1, EQUIPO_1, 10, "2026-09-23T13:00:00", 2)
        + commits(2, ["Elena Ríos", "Carlos León"], 12, "2026-09-21T15:00:00", 30)
        + tareas_p2()
        + documentos(2, ["Elena Ríos", "Carlos León"], 6, "2026-09-10T13:00:00", 3)
    )
    return {
        "_comentario": "TA-017. Generado por backend/scripts/generar_dataset_demo.py; no editar a mano.",
        "fecha_corte": iso(FECHA_CORTE),
        "proyectos": [
            {"id": 1, "nombre": "Seguimiento académico", "escenario": "activo: dispara R1 y R2"},
            {"id": 2, "nombre": "Biblioteca digital", "escenario": "estancado: dispara R3 y R4 (y también R1 y R2)"},
        ],
        "evidencias": evidencias,
        "indicadores_esperados": {str(p): evaluar_con_motor(evidencias, p)[0] for p in (1, 2)},
        "alertas_esperadas": {str(p): evaluar_con_motor(evidencias, p)[1] for p in (1, 2)},
    }


if __name__ == "__main__":
    datos = construir()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for pid in ("1", "2"):
        reglas = sorted({a["regla"] for a in datos["alertas_esperadas"][pid]})
        n = sum(1 for e in datos["evidencias"] if str(e["proyecto_id"]) == pid)
        print(f"proyecto {pid}: {n} evidencias, reglas disparadas: {reglas}")
        print(f"            indicadores: {datos['indicadores_esperados'][pid]}")
    print(f"escrito: {SALIDA}")
