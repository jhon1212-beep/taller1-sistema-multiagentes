# -*- coding: utf-8 -*-
"""AR-05 · EjecutorE2EFalso.

Implementa el puerto EjecutorE2E sin GitHub Actions ni red, para que el
Supervisor registre validaciones antes de que exista el Agente de Validación
real (TA-021). Es determinista: la URL decide el resultado.

- Si `url_publica` contiene "falla" → FAIL con captura de ejemplo.
- En cualquier otro caso → PASS.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from app.modulos.validacion.dominio import ResultadoValidacion, SolicitudValidacion

RUN_ID_FALSO = 1_000_000_001  # identificador fijo de la ejecución simulada


class EjecutorE2EFalso:
    def __init__(self, *, ahora: Callable[[], datetime] | None = None) -> None:
        self._ahora = ahora or (lambda: datetime.now(timezone.utc))

    def ejecutar(self, solicitud: SolicitudValidacion) -> ResultadoValidacion:
        falla = "falla" in solicitud.url_publica.lower()
        return ResultadoValidacion(
            proyecto_id=solicitud.proyecto_id,
            resultado="FAIL" if falla else "PASS",
            duracion_ms=1200,
            ejecutada_en=self._ahora(),
            run_id_actions=RUN_ID_FALSO,
            captura_url=(
                f"https://ejemplo.invalid/artefactos/{RUN_ID_FALSO}/captura.png" if falla else None
            ),
        )
