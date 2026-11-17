"""RN-003: comprueba la trazabilidad de los resultados guardados en PostgreSQL.

Criterios del Product Backlog v6.0:
  1) 100 % de las alertas guarda el id de su evidencia.
  2) 100 % de las validaciones guarda el id de su ejecución en GitHub Actions.

Ejecuta las consultas de docs/sprint2/RN-003_trazabilidad.sql sobre la base de
DATABASE_URL, imprime el checklist y lo guarda en
docs/sprint2/evidencias/RN-003_checklist.md. Termina con código 1 si algún
criterio no llega al 100 %.

Uso, desde la raíz del repositorio y con el entorno virtual activo:
    python backend/scripts/verificar_trazabilidad.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from sqlalchemy import create_engine, text  # noqa: E402

from app.compartido.config import obtener_database_url  # noqa: E402

SALIDA = RAIZ / "docs" / "sprint2" / "evidencias" / "RN-003_checklist.md"

CONSULTAS = {
    "alertas": "SELECT COUNT(*), COUNT(*) FILTER (WHERE e.id IS NULL) "
               "FROM alerta a LEFT JOIN evidencia e ON e.id = a.evidencia_id",
    "alertas_otro_proyecto": "SELECT COUNT(*) FROM alerta a JOIN evidencia e ON e.id = a.evidencia_id "
                             "WHERE e.proyecto_id <> a.proyecto_id",
    "alertas_otra_fuente": "SELECT COUNT(*) FROM alerta a JOIN evidencia e ON e.id = a.evidencia_id "
                           "JOIN fuente f ON f.id = e.fuente_id "
                           "WHERE (a.regla IN ('R1','R2') AND f.tipo <> 'notion') "
                           "OR (a.regla = 'R3' AND f.tipo <> 'github') OR (a.regla = 'R4' AND f.tipo <> 'drive')",
    "validaciones": "SELECT COUNT(*), COUNT(*) FILTER (WHERE run_id_actions IS NULL OR run_id_actions <= 0) "
                    "FROM validacion",
    "fail": "SELECT COUNT(*) FILTER (WHERE resultado = 'FAIL'), "
            "COUNT(*) FILTER (WHERE resultado = 'FAIL' AND captura_url IS NULL) FROM validacion",
}


def porcentaje(total: int, malas: int) -> str:
    return "sin registros" if total == 0 else f"{100 * (total - malas) / total:.0f} %"


def main() -> int:
    with create_engine(obtener_database_url()).connect() as conexion:
        r = {k: conexion.execute(text(q)).one() for k, q in CONSULTAS.items()}

    total_alertas, alertas_sin = r["alertas"]
    otra_proyecto, otra_fuente = r["alertas_otro_proyecto"][0], r["alertas_otra_fuente"][0]
    total_val, val_sin = r["validaciones"]
    total_fail, fail_sin_captura = r["fail"]

    malas_alertas = alertas_sin + otra_proyecto + otra_fuente
    ok1 = total_alertas > 0 and malas_alertas == 0
    ok2 = total_val > 0 and val_sin == 0
    marca = lambda ok: "x" if ok else " "  # noqa: E731
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime("%d/%m/%Y %H:%M")

    lineas = [
        "# RN-003 · Checklist de trazabilidad",
        "",
        f"Generado el {ahora} (hora de Lima) con `backend/scripts/verificar_trazabilidad.py`.",
        "",
        "| Criterio | Registros | Sin traza | Resultado |",
        "|---|---|---|---|",
        f"| Alertas con el id de su evidencia | {total_alertas} | {alertas_sin} | {porcentaje(total_alertas, alertas_sin)} |",
        f"| Evidencia del mismo proyecto que la alerta | {total_alertas} | {otra_proyecto} | {porcentaje(total_alertas, otra_proyecto)} |",
        f"| Evidencia de la fuente que exige la regla | {total_alertas} | {otra_fuente} | {porcentaje(total_alertas, otra_fuente)} |",
        f"| Validaciones con el id de su ejecución en Actions | {total_val} | {val_sin} | {porcentaje(total_val, val_sin)} |",
        f"| Validaciones FAIL con captura (informativo) | {total_fail} | {fail_sin_captura} | {porcentaje(total_fail, fail_sin_captura)} |",
        "",
        f"- [{marca(ok1)}] 1) 100 % de las alertas guarda el id de su evidencia.",
        f"- [{marca(ok2)}] 2) 100 % de las validaciones guarda el id de su ejecución en GitHub Actions.",
        "",
        "Garantía estructural: `alerta.evidencia_id` es una clave foránea obligatoria hacia `evidencia`, "
        "`validacion.run_id_actions` es obligatorio, y el repositorio no guarda una alerta cuya evidencia "
        "no exista (la cuenta en `alertas_sin_evidencia`).",
    ]
    if total_alertas == 0 or total_val == 0:
        lineas += ["", "Faltan registros: ejecutar al menos una supervisión y una validación antes de auditar."]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    print(f"\nGuardado en {SALIDA.relative_to(RAIZ)}")
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
