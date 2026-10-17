# -*- coding: utf-8 -*-
"""
TA-011 · Auditoría de consistencia de la interfaz

Comprueba de forma automática que la UI respete el sistema visual:
  1. Tokens declarados en tokens.css que nadie usa.
  2. Tokens usados que no están declarados (romperían el estilo).
  3. Colores escritos a mano (hex) fuera de tokens.css.
  4. Tamaños de fuente en px escritos a mano fuera de tokens.css.

Uso:  python scripts/auditar_ui.py
Salida: docs/sprint1/TA-011_auditoria.json  y resumen por consola.
Código de salida 1 si hay hallazgos de severidad alta.
"""
from __future__ import annotations

import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(RAIZ, "frontend", "src", "estilos", "tokens.css")

# Archivos de interfaz que deben consumir el sistema visual.
OBJETIVOS = [
    os.path.join(RAIZ, "frontend", "src"),
    os.path.join(RAIZ, "docs", "Prototipo_Agentes_Seguimiento.html"),
]
EXTENSIONES = (".css", ".jsx", ".js", ".html")

# Excepciones justificadas: no son parte de la paleta.
HEX_PERMITIDOS = {"#fff", "#ffffff", "#000", "#000000"}


def recolectar(rutas):
    archivos = []
    for ruta in rutas:
        if os.path.isfile(ruta):
            archivos.append(ruta)
        elif os.path.isdir(ruta):
            for base, _, nombres in os.walk(ruta):
                if "node_modules" in base or "dist" in base:
                    continue
                archivos += [os.path.join(base, n) for n in nombres if n.endswith(EXTENSIONES)]
    return archivos


def rel(p):
    return os.path.relpath(p, RAIZ).replace("\\", "/")


def main() -> int:
    if not os.path.exists(TOKENS):
        print(f"No se encontró {rel(TOKENS)}")
        return 1

    css_tokens = open(TOKENS, encoding="utf-8").read()
    # Varias declaraciones pueden ir en la misma línea (--sp-1: 4px; --sp-2: 8px;),
    # por eso no se ancla la búsqueda al inicio de línea.
    declarados = set(re.findall(r"(--[\w-]+)\s*:", css_tokens))

    archivos = [a for a in recolectar(OBJETIVOS) if os.path.abspath(a) != os.path.abspath(TOKENS)]

    usados: dict[str, int] = {}
    hex_sueltos: list[dict] = []
    px_fuente: list[dict] = []

    for archivo in archivos:
        texto = open(archivo, encoding="utf-8", errors="replace").read()

        for token in re.findall(r"var\((--[\w-]+)", texto):
            usados[token] = usados.get(token, 0) + 1

        for linea_n, linea in enumerate(texto.splitlines(), 1):
            for hx in re.findall(r"#[0-9a-fA-F]{3,8}\b", linea):
                if hx.lower() in HEX_PERMITIDOS:
                    continue
                # ignora anclas/ids de HTML y rutas
                if re.search(r'(href|id|name)\s*=\s*["\']?' + re.escape(hx), linea):
                    continue
                hex_sueltos.append({"archivo": rel(archivo), "linea": linea_n, "valor": hx})
            for px in re.findall(r"font-size:\s*(\d+(?:\.\d+)?px)", linea):
                px_fuente.append({"archivo": rel(archivo), "linea": linea_n, "valor": px})

    # tokens que se usan internamente dentro de tokens.css (p. ej. --infobg: var(--soft))
    usados_internos = set(re.findall(r"var\((--[\w-]+)", css_tokens))

    sin_usar = sorted(declarados - set(usados) - usados_internos)
    sin_declarar = sorted(set(usados) - declarados)

    hallazgos = {
        "tokens_declarados": len(declarados),
        "tokens_usados": len(set(usados) & declarados),
        "archivos_revisados": len(archivos),
        "tokens_sin_usar": sin_usar,
        "tokens_sin_declarar": sin_declarar,
        "colores_hardcodeados": hex_sueltos,
        "font_size_hardcodeado": px_fuente,
    }

    os.makedirs(os.path.join(RAIZ, "docs", "sprint1"), exist_ok=True)
    salida = os.path.join(RAIZ, "docs", "sprint1", "TA-011_auditoria.json")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(hallazgos, fh, ensure_ascii=False, indent=2)

    print("=" * 58)
    print("TA-011 · Auditoría de consistencia de la interfaz")
    print("=" * 58)
    print(f"Archivos de UI revisados : {len(archivos)}")
    print(f"Tokens declarados        : {len(declarados)}")
    print(f"Tokens en uso            : {len(set(usados) & declarados)}")
    print(f"Tokens sin usar          : {len(sin_usar)}  {sin_usar if sin_usar else ''}")
    print(f"Tokens sin declarar      : {len(sin_declarar)}  {sin_declarar if sin_declarar else ''}")
    print(f"Colores escritos a mano  : {len(hex_sueltos)}")
    for h in hex_sueltos[:8]:
        print(f"    {h['archivo']}:{h['linea']}  {h['valor']}")
    print(f"font-size en px a mano   : {len(px_fuente)}")
    for h in px_fuente[:8]:
        print(f"    {h['archivo']}:{h['linea']}  {h['valor']}")
    print("-" * 58)
    print(f"Detalle: {rel(salida)}")

    # Severidad alta: un token usado que no existe rompe el estilo.
    return 1 if sin_declarar else 0


if __name__ == "__main__":
    raise SystemExit(main())
