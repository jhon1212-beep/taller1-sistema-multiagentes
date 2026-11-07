"""Convierte la referencia registrada de una fuente en el identificador que pide su API.

El formulario de HU-002 guarda los enlaces tal como el docente los copia del
navegador, pero cada API necesita otra cosa:

    GitHub  https://github.com/org/repo(.git)        -> "org/repo"
    Notion  https://app.notion.com/p/Nombre-<32 hex>  -> "<32 hex>" (id de la base)
            https://www.notion.so/<espacio>/<32 hex>?v=...
    Drive   https://drive.google.com/drive/folders/<id>?usp=sharing -> "<id>"
            https://drive.google.com/open?id=<id>

Si la referencia ya es un identificador ("org/repo", el id suelto, "dataset:1"),
se devuelve igual. Así los proyectos registrados antes siguen funcionando.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


def repositorio_github(referencia: str) -> str:
    ref = (referencia or "").strip()
    if not ref.lower().startswith(("http://", "https://", "github.com/", "www.github.com/")):
        return ref
    url = urlparse(ref if "://" in ref else f"https://{ref}")
    partes = [p for p in url.path.split("/") if p]
    if len(partes) < 2:
        return ref
    return f"{partes[0]}/{partes[1].removesuffix('.git')}"


def base_notion(referencia: str) -> str:
    ref = (referencia or "").strip()
    if "/" not in ref and "?" not in ref:
        return ref
    # El id de la base va al final del último segmento de la ruta, con o sin
    # guiones («Nombre-<32 hex>» o un UUID). El «?v=» de la vista es otro id y
    # se descarta al quedarse solo con la ruta.
    segmentos = [p for p in urlparse(ref).path.split("/") if p]
    if not segmentos:
        return ref
    ultimo = segmentos[-1]
    uuid = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$", ultimo)
    if uuid:
        return uuid.group(1)
    hex32 = re.search(r"([0-9a-fA-F]{32})$", ultimo)
    return hex32.group(1) if hex32 else ref


def carpeta_drive(referencia: str) -> str:
    ref = (referencia or "").strip()
    if "/" not in ref and "?" not in ref:
        return ref
    url = urlparse(ref)
    coincidencia = re.search(r"/folders/([\w-]+)", url.path)
    if coincidencia:
        return coincidencia.group(1)
    ids = parse_qs(url.query).get("id")
    return ids[0] if ids else ref
