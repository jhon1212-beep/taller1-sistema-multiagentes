# -*- coding: utf-8 -*-
"""HU-006 · Hoja de cálculo que reproduce I1–I4 con fórmulas de Excel.

Toma las evidencias del dataset de TA-017 y la fecha de corte, calcula los cuatro
indicadores de cada proyecto con fórmulas (COUNTIF, MAXIFS, ...) y los compara con
lo que muestra el Dashboard (HU-006_valores_dashboard.json, que escribe
frontend/scripts/capturar-semana10.mjs leyendo la pantalla).

    python backend/scripts/generar_hoja_indicadores.py

Salida: docs/sprint2/evidencias/semana10/HU-006_indicadores.xlsx
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from app.modulos.evidencias.dataset import cargar_dataset  # noqa: E402

CARPETA = RAIZ / "docs" / "sprint2" / "evidencias" / "semana10"
SALIDA = CARPETA / "HU-006_indicadores.xlsx"

AZUL = PatternFill("solid", fgColor="1F3864")
GRIS = PatternFill("solid", fgColor="F2F2F2")
VERDE = PatternFill("solid", fgColor="E2F0D9")
BORDE = Border(*(Side(style="thin", color="BFBFBF"),) * 4)


def _dt(texto: str) -> datetime:
    """Datetime ingenuo en UTC (Excel no guarda zona horaria)."""
    return datetime.fromisoformat(texto.replace("Z", "+00:00")).replace(tzinfo=None)


def _encabezado(hoja, fila: int, titulos: list[str]) -> None:
    for col, t in enumerate(titulos, start=1):
        c = hoja.cell(row=fila, column=col, value=t)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = AZUL
        c.border = BORDE
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _ancho(hoja, anchos: list[int]) -> None:
    for col, a in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(col)].width = a


def construir() -> Workbook:
    datos = cargar_dataset()
    corte = _dt(datos["fecha_corte"])
    mostrado = json.loads((CARPETA / "HU-006_valores_dashboard.json").read_text(encoding="utf-8"))
    wb = Workbook()
    ind = wb.active
    ind.title = "Indicadores"

    ind["A1"] = "HU-006 · Indicadores I1–I4 calculados con fórmulas"
    ind["A1"].font = Font(bold=True, size=14, color="1F3864")
    ind["A3"], ind["B3"] = "Fecha de corte (UTC)", corte
    ind["B3"].number_format = "dd/mm/yyyy hh:mm:ss"
    ind["A4"] = "Origen de las evidencias"
    ind["B4"] = "Dataset de TA-017 (hojas Tareas_P* y Actividad_P*). «Dashboard» = lo leído de la pantalla."
    for celda in ("A3", "A4"):
        ind[celda].font = Font(bold=True)

    _encabezado(ind, 6, ["Indicador", "Fórmula", "P1 · hoja", "P1 · Dashboard", "¿Coincide?",
                         "P2 · hoja", "P2 · Dashboard", "¿Coincide?"])
    filas = {"I1": 7, "I2": 8, "I3": 9, "I4": 10}
    formulas = {
        "I1": "tareas «Listo» ÷ total de tareas × 100",
        "I2": "tareas «Sin empezar» o «En curso» ÷ total × 100",
        "I3": "tareas no «Listo» con fecha límite anterior al día de corte",
        "I4": "días completos entre la última evidencia y el corte",
    }

    for pid, nombre_hoja in ((1, "P1"), (2, "P2")):
        col_hoja = 3 if pid == 1 else 6
        col_dash = col_hoja + 1
        letra = lambda c: get_column_letter(c)  # noqa: E731
        evs = [e for e in datos["evidencias"] if e["proyecto_id"] == pid]
        tareas = [e for e in evs if e["fuente"] == "notion"]

        # --- hoja de tareas -------------------------------------------------
        ht = wb.create_sheet(f"Tareas_{nombre_hoja}")
        _encabezado(ht, 1, ["id", "Tarea", "Responsable", "Estado", "Fecha límite", "Última edición (UTC)",
                            "¿Vencida? (1 = sí)"])
        for i, t in enumerate(tareas, start=2):
            ht.cell(row=i, column=1, value=t["id_externo"])
            ht.cell(row=i, column=2, value=t["descripcion"])
            ht.cell(row=i, column=3, value=t["autor"])
            ht.cell(row=i, column=4, value=t["estado"])
            ht.cell(row=i, column=5, value=date.fromisoformat(t["fecha_limite"])).number_format = "dd/mm/yyyy"
            ht.cell(row=i, column=6, value=_dt(t["fecha"])).number_format = "dd/mm/yyyy hh:mm"
            ht.cell(row=i, column=7, value=f'=IF(AND(D{i}<>"Listo",E{i}<INT(Indicadores!$B$3)),1,0)')
        ultima_t = len(tareas) + 1
        _ancho(ht, [14, 34, 16, 14, 14, 20, 16])
        ht.freeze_panes = "A2"

        # --- hoja de actividad (todas las fuentes, para I4) ------------------
        ha = wb.create_sheet(f"Actividad_{nombre_hoja}")
        _encabezado(ha, 1, ["id", "Fuente", "Descripción", "Fecha (UTC)"])
        for i, e in enumerate(evs, start=2):
            ha.cell(row=i, column=1, value=e["id_externo"][:12])
            ha.cell(row=i, column=2, value=e["fuente"])
            ha.cell(row=i, column=3, value=e["descripcion"])
            ha.cell(row=i, column=4, value=_dt(e["fecha"])).number_format = "dd/mm/yyyy hh:mm"
        ultima_a = len(evs) + 1
        _ancho(ha, [16, 10, 40, 20])
        ha.freeze_panes = "A2"

        t, a = f"Tareas_{nombre_hoja}", f"Actividad_{nombre_hoja}"
        ind.cell(row=filas["I1"], column=col_hoja,
                 value=f'=COUNTIF({t}!D2:D{ultima_t},"Listo")/COUNTA({t}!D2:D{ultima_t})*100')
        ind.cell(row=filas["I2"], column=col_hoja,
                 value=f'=(COUNTA({t}!D2:D{ultima_t})-COUNTIF({t}!D2:D{ultima_t},"Listo"))/COUNTA({t}!D2:D{ultima_t})*100')
        ind.cell(row=filas["I3"], column=col_hoja, value=f"=SUM({t}!G2:G{ultima_t})")
        ind.cell(row=filas["I4"], column=col_hoja,
                 value=f'=INT($B$3-_xlfn.MAXIFS({a}!D2:D{ultima_a},{a}!D2:D{ultima_a},"<="&$B$3))')

        for clave, fila in filas.items():
            texto = mostrado[str(pid)][clave].replace("%", "").replace(",", ".").strip()
            ind.cell(row=fila, column=col_dash, value=float(texto))
            ind.cell(row=fila, column=col_dash + 1,
                     value=f'=IF(ABS({letra(col_hoja)}{fila}-{letra(col_dash)}{fila})<0.01,"Sí","NO")')

    for clave, fila in filas.items():
        ind.cell(row=fila, column=1, value=clave).font = Font(bold=True)
        ind.cell(row=fila, column=2, value=formulas[clave])
        for col in range(1, 9):
            c = ind.cell(row=fila, column=col)
            c.border = BORDE
            if col in (3, 6):
                c.number_format = "0.00" if clave in ("I1", "I2") else "0"
                c.fill = VERDE
            if col in (4, 7):
                c.number_format = "0.00" if clave in ("I1", "I2") else "0"
            if col in (5, 8):
                c.alignment = Alignment(horizontal="center")
    ind["A12"] = "Notas"
    ind["A12"].font = Font(bold=True)
    ind["A13"] = ("I2 cuenta como pendiente toda tarea que no está «Listo» (sin empezar y en curso), que es la "
                  "definición del motor que usa el Supervisor (motor_indicadores.py). El dataset y la documentación "
                  "de TA-019 definen I2 solo como «Sin empezar»: ver el informe, sección de inconsistencias.")
    ind["A13"].alignment = Alignment(wrap_text=True, vertical="top")
    ind.merge_cells("A13:H15")
    _ancho(ind, [24, 52, 12, 16, 12, 12, 16, 12])
    ind.row_dimensions[6].height = 30
    return wb


if __name__ == "__main__":
    wb = construir()
    wb.save(SALIDA)
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")
