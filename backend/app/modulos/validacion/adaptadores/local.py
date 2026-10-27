# -*- coding: utf-8 -*-
"""TA-021 · EjecutorE2ELocal: corre e2e/validar-url.mjs en esta máquina.

Es el mismo script que ejecuta el workflow TA-047, con los mismos parámetros por
variables de entorno, pero sin GitHub Actions. Sirve para desarrollar y para probar
el Agente de Validación antes de tener el repositorio remoto.

`run_id_actions` es NEGATIVO (-epoch en segundos) para que una ejecución local nunca
se confunda con un run real de Actions (RN-003 exige el campo, no que sea positivo).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from app.compartido.config import RAIZ
from app.modulos.validacion.dominio import (
    ErrorInfraestructuraValidacion,
    ResultadoValidacion,
    SolicitudValidacion,
)


class EjecutorE2ELocal:
    def __init__(
        self,
        *,
        carpeta_e2e: Path | None = None,
        canal: str | None = None,
        salida_base: Path | None = None,
    ):
        self._e2e = carpeta_e2e or RAIZ / "e2e"
        self._canal = canal if canal is not None else os.getenv("E2E_CANAL", "")
        self._base = salida_base

    def ejecutar(self, solicitud: SolicitudValidacion) -> ResultadoValidacion:
        node = shutil.which("node")
        if not node:
            raise ErrorInfraestructuraValidacion("No se encontró Node.js en el PATH.")
        run_id = -int(time.time())
        salida = (self._base or Path(tempfile.gettempdir())) / f"validacion_{abs(run_id)}"
        entorno = {
            **os.environ,
            "URL_PUBLICA": solicitud.url_publica,
            "ELEMENTO_VERIFICAR": solicitud.elemento_verificar,
            "PROYECTO_ID": str(solicitud.proyecto_id),
            "SALIDA": str(salida),
            "E2E_CANAL": self._canal,
        }
        proceso = subprocess.run(
            [node, "validar-url.mjs"],
            cwd=self._e2e,
            env=entorno,
            capture_output=True,
            text=True,
            timeout=120,
        )
        archivo = salida / "resultado.json"
        if proceso.returncode not in (0, 1) or not archivo.exists():
            raise ErrorInfraestructuraValidacion(
                f"El script E2E no produjo resultado (código {proceso.returncode}): "
                f"{proceso.stderr.strip()[:300]}"
            )
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        captura = salida / "captura.png"
        return ResultadoValidacion(
            proyecto_id=solicitud.proyecto_id,
            resultado=datos["resultado"],
            duracion_ms=int(datos["duracion_ms"]),
            ejecutada_en=datetime.fromisoformat(datos["ejecutada_en"].replace("Z", "+00:00")),
            run_id_actions=run_id,
            captura_url=captura.as_uri() if datos["resultado"] == "FAIL" and captura.exists() else None,
        )
