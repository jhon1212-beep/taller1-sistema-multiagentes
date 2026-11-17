"""R5: coherencia entre el mensaje de un commit y lo que el commit cambió.

Regla determinista: compara el mensaje con los nombres de los archivos y las
líneas modificadas. No lee el código ni usa un LLM para decidir (la IA solo
redacta la explicación, como en R1–R4). Devuelve un motivo legible o None.

La alerta es una **posible incoherencia para revisar**, no una prueba de que el
estudiante mintió: un mensaje mal redactado o un squash también la disparan.
Por eso solo se revisan casos objetivos:

    1. El commit no cambia el contenido de ningún archivo.
    2. El mensaje dice haber escrito pruebas y no se tocó nada relacionado
       con pruebas (ninguna ruta con test, spec, e2e o prueba).
    3. El mensaje anuncia código (feat, fix, implementa…) y solo cambió
       documentación o imágenes.
    4. El mensaje nombra un archivo (Login.jsx, servicio.py…) que no se modificó.

Los merges (más de un padre) y los commits sin detalle no se evalúan.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Sequence

MAX_ARCHIVOS_EN_MOTIVO = 4

# Afirma haber escrito pruebas: prefijo «test:» o un verbo seguido de pruebas/tests.
# «plan de pruebas», «informe de pruebas»… son documentación y no cuentan.
_PRUEBAS_EN_MENSAJE = re.compile(
    r"^tests?(\(.+?\))?!?:"
    r"|\b(agrega|añade|anade|crea|escribe|implementa|automatiza|add|adds|write|writes)\b[^.]*\b(pruebas?|tests?)\b",
    re.IGNORECASE,
)
_DOCUMENTA_PRUEBAS = re.compile(r"^docs?(\(.+?\))?!?:|\b(plan|informe|documento|protocolo|reporte)\b", re.IGNORECASE)
# Cualquier ruta con «test», «spec», «e2e» o «prueba» cuenta como relacionada con pruebas.
_ARCHIVO_DE_PRUEBA = re.compile(r"tests?|spec|e2e|prueba", re.IGNORECASE)
_ANUNCIA_CODIGO = re.compile(
    r"^(feat|fix|refactor|perf)(\(.+?\))?!?:|^(implementa|agrega|añade|anade|crea|corrige|arregla|refactoriza)\b",
    re.IGNORECASE,
)
_NO_CODIGO = re.compile(r"\.(md|txt|rst|pdf|docx?|odt|pptx?|xlsx?|png|jpe?g|gif|svg|webp)$", re.IGNORECASE)
_ARCHIVO_EN_MENSAJE = re.compile(
    r"[\w./-]*?([\w-]+\.(?:py|jsx?|tsx?|java|cs|php|rb|go|kt|swift|css|scss|html|sql|json|ya?ml|md))\b",
    re.IGNORECASE,
)


def _lista(archivos: Sequence[str]) -> str:
    nombres = ", ".join(archivos[:MAX_ARCHIVOS_EN_MOTIVO])
    resto = len(archivos) - MAX_ARCHIVOS_EN_MOTIVO
    return f"{nombres} y {resto} más" if resto > 0 else nombres


def revisar_commit(
    mensaje: str,
    archivos: Sequence[str] | None,
    adiciones: int | None = None,
    eliminaciones: int | None = None,
    es_merge: bool = False,
) -> str | None:
    """Motivo de la posible incoherencia, o None si el commit es coherente o no se evalúa."""
    if archivos is None or es_merge:
        return None
    mensaje = (mensaje or "").strip()
    cita = f"«{mensaje[:120]}»"

    if not archivos or (adiciones or 0) + (eliminaciones or 0) == 0:
        return (f"El commit {cita} no cambia el contenido de ningún archivo "
                "(está vacío o solo mueve o renombra archivos).")

    if (_PRUEBAS_EN_MENSAJE.search(mensaje) and not _DOCUMENTA_PRUEBAS.search(mensaje)
            and not any(_ARCHIVO_DE_PRUEBA.search(a) for a in archivos)):
        return (f"El mensaje {cita} dice agregar pruebas, pero no se modificó ningún archivo de "
                f"pruebas. Archivos modificados: {_lista(archivos)}.")

    if _ANUNCIA_CODIGO.search(mensaje) and all(_NO_CODIGO.search(a) for a in archivos):
        return (f"El mensaje {cita} anuncia un cambio de código, pero solo se modificó "
                f"documentación o imágenes: {_lista(archivos)}.")

    modificados = {PurePosixPath(a).name.casefold() for a in archivos}
    for nombre in dict.fromkeys(m.group(1) for m in _ARCHIVO_EN_MENSAJE.finditer(mensaje)):
        if nombre.casefold() not in modificados:
            return (f"El mensaje {cita} menciona el archivo «{nombre}», pero ese archivo no está "
                    f"entre los modificados: {_lista(archivos)}.")
    return None
