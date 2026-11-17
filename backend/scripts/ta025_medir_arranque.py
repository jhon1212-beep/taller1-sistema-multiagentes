"""TA-025: mide el arranque en frío del backend desplegado (Render Free).

El plan gratuito duerme el servicio tras ~15 min sin tráfico. Este script mide
la primera respuesta (arranque en frío) y luego varias respuestas en caliente.

Uso (después de 20 min o más sin abrir la API):

    python backend/scripts/ta025_medir_arranque.py --url https://grupo8-backend.onrender.com
    python backend/scripts/ta025_medir_arranque.py --url ... --correo docente@... --clave ...

Con --correo y --clave también mide el inicio de sesión y GET /proyectos.
Escribe docs/sprint2/evidencias/TA-025_arranque.json y .md. No guarda la clave.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / "docs" / "sprint2" / "evidencias"
CALIENTES = 3  # /health admite 5 peticiones por minuto: 1 en frío + 3 en caliente


def _peticion(url: str, *, datos: dict | None = None, token: str | None = None,
              timeout: float = 180) -> tuple[int, float, dict | list | None]:
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    cuerpo = json.dumps(datos).encode() if datos is not None else None
    req = urllib.request.Request(url, data=cuerpo, headers=cabeceras, method="POST" if cuerpo else "GET")
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            texto = resp.read().decode()
            codigo = resp.status
    except urllib.error.HTTPError as err:
        texto, codigo = err.read().decode(errors="replace"), err.code
    ms = round((time.perf_counter() - inicio) * 1000, 1)
    try:
        return codigo, ms, json.loads(texto) if texto else None
    except ValueError:
        return codigo, ms, None


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", required=True, help="URL base del backend, sin barra final")
    p.add_argument("--correo")
    p.add_argument("--clave")
    args = p.parse_args()
    base = args.url.rstrip("/")

    print("Midiendo el arranque en frío (puede tardar cerca de 1 minuto)…", flush=True)
    codigo, frio_ms, _ = _peticion(f"{base}/health")
    medidas = {"frio": {"ruta": "/health", "codigo": codigo, "ms": frio_ms}, "caliente": []}
    for _ in range(CALIENTES):
        time.sleep(1)
        codigo, ms, _ = _peticion(f"{base}/health")
        medidas["caliente"].append({"ruta": "/health", "codigo": codigo, "ms": ms})

    if args.correo and args.clave:
        codigo, ms, cuerpo = _peticion(f"{base}/auth/login", datos={"correo": args.correo, "password": args.clave})
        medidas["login"] = {"codigo": codigo, "ms": ms}
        token = (cuerpo or {}).get("token") if isinstance(cuerpo, dict) else None
        if token:
            codigo, ms, cuerpo = _peticion(f"{base}/proyectos", token=token)
            medidas["proyectos"] = {"codigo": codigo, "ms": ms,
                                    "total": len(cuerpo) if isinstance(cuerpo, list) else None}

    calientes = [m["ms"] for m in medidas["caliente"]]
    resultado = {
        "url": base,
        "fecha": datetime.now(ZoneInfo("America/Lima")).isoformat(timespec="seconds"),
        **medidas,
        "caliente_promedio_ms": round(sum(calientes) / len(calientes), 1),
    }
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "TA-025_arranque.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")
    filas = [f"| Arranque en frío (/health) | {medidas['frio']['codigo']} | {frio_ms / 1000:.1f} s |"]
    filas += [f"| En caliente {i} (/health) | {m['codigo']} | {m['ms']:.0f} ms |"
              for i, m in enumerate(medidas["caliente"], 1)]
    if "login" in medidas:
        filas.append(f"| POST /auth/login | {medidas['login']['codigo']} | {medidas['login']['ms']:.0f} ms |")
    if "proyectos" in medidas:
        filas.append(f"| GET /proyectos | {medidas['proyectos']['codigo']} | {medidas['proyectos']['ms']:.0f} ms |")
    tabla = "| Medición | HTTP | Tiempo |\n|---|---|---|\n" + "\n".join(filas)
    (DESTINO / "TA-025_arranque.md").write_text(
        f"# TA-025 · Arranque en frío del backend\n\nURL: {base} · Fecha: {resultado['fecha']}\n\n{tabla}\n",
        encoding="utf-8")
    print("\n" + tabla)
    print(f"\nGuardado en {DESTINO / 'TA-025_arranque.json'} y .md")


if __name__ == "__main__":
    main()
