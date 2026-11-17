"""TA-029: verifica las fuentes de un proyecto piloto antes de registrarlo.

Usa los mismos adaptadores reales que el Supervisor, así que si aquí sale
"ok", el corte también podrá leer esa fuente. Drive es opcional.

Uso (desde la raíz, con GITHUB_TOKEN, NOTION_TOKEN/NOTION_TOKENS y, si hay Drive,
GOOGLE_SERVICE_ACCOUNT_JSON en el .env):

    python backend/scripts/ta029_verificar_fuentes.py --proyecto "Grupo A" \
        --github https://github.com/org/repo \
        --notion https://www.notion.so/<id-de-la-base> \
        [--drive https://drive.google.com/drive/folders/<id>]

Escribe docs/sprint2/evidencias/TA-029_<proyecto>.json con, por fuente: estado,
cantidad de evidencias, fecha de la más reciente y el error si lo hubo. No
guarda nombres de integrantes (solo cuántos autores distintos hay).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
BACKEND = RAIZ / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
load_dotenv(RAIZ / ".env")

from app.modulos.supervision.sources import build_source_adapters  # noqa: E402

DESTINO = RAIZ / "docs" / "sprint2" / "evidencias"


def _verificar(adaptador, referencia: str) -> dict:
    inicio = time.perf_counter()
    try:
        evidencias = adaptador.obtener_evidencias(referencia=referencia, proyecto_id=0)
    except Exception as error:  # se informa, no se detiene: puede fallar solo una fuente
        return {"estado": "fallo", "error": f"{type(error).__name__}: {error}",
                "ms": round((time.perf_counter() - inicio) * 1000)}
    fechas = sorted(e.fecha for e in evidencias if e.fecha)
    return {
        "estado": "ok",
        "evidencias": len(evidencias),
        "autores_distintos": len({e.autor for e in evidencias if e.autor}),
        "mas_reciente": fechas[-1] if fechas else None,
        "ms": round((time.perf_counter() - inicio) * 1000),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proyecto", required=True, help="nombre corto del proyecto piloto")
    p.add_argument("--github", required=True)
    p.add_argument("--notion", required=True)
    p.add_argument("--drive", default="", help="opcional")
    args = p.parse_args()

    adaptadores = build_source_adapters("real")
    referencias = {"github": args.github, "notion": args.notion}
    if args.drive.strip():
        referencias["drive"] = args.drive.strip()

    fuentes = {}
    for tipo, referencia in referencias.items():
        print(f"Verificando {tipo}…", flush=True)
        fuentes[tipo] = {"referencia": referencia, **_verificar(adaptadores[tipo], referencia)}
    if "drive" not in referencias:
        fuentes["drive"] = {"estado": "no_configurada"}

    listo = all(fuentes[t]["estado"] == "ok" for t in referencias)
    resultado = {
        "proyecto": args.proyecto,
        "fecha": datetime.now(ZoneInfo("America/Lima")).isoformat(timespec="seconds"),
        "listo_para_registrar": listo,
        "fuentes": fuentes,
    }
    nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", args.proyecto).strip("_") or "proyecto"
    DESTINO.mkdir(parents=True, exist_ok=True)
    destino = DESTINO / f"TA-029_{nombre}.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for tipo, f in fuentes.items():
        detalle = f.get("error") or (f"{f['evidencias']} evidencias, última {f['mas_reciente']}"
                                     if f["estado"] == "ok" else "")
        print(f"  {tipo:7} {f['estado']:15} {detalle}")
    print(f"\n{'LISTO' if listo else 'REVISAR'}: {destino}")
    if not listo:
        print("Revisa los permisos en docs/sprint2/Conectar_fuentes_de_otro_equipo.md")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
