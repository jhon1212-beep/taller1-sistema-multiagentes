"""TA-030: estabilidad de los agentes de fuente con datos reales.

Las APIs reales (GitHub, Notion, Drive) fallan a veces por causas pasajeras: un
5xx, un 429 o un corte de red. Antes, un solo error de ese tipo dejaba la fuente
en "fallo" para todo el corte. Aquí se define:

- qué errores son transitorios (se reintentan) y cuáles no (credenciales,
  permisos, referencia mal escrita: reintentar no los arregla);
- un reintento con espera corta;
- un tiempo máximo por fuente, para que una API colgada no deje al docente
  esperando la respuesta de «Ejecutar supervisión».

Valores por variables de entorno (se leen al armar el grafo):

    SUPERVISION_SOURCE_ATTEMPTS   intentos por fuente           (por defecto 2)
    SUPERVISION_RETRY_BACKOFF_S   espera antes de reintentar    (por defecto 2)
    SUPERVISION_SOURCE_TIMEOUT_S  tiempo máximo por fuente      (por defecto 90)
"""
from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

# Mensajes que dejan los clientes de evidencias (HTTP 5xx, 429, red, tiempo agotado).
_TRANSIENT = re.compile(
    r"HTTP (5\d\d|429)|Error de red|timed out|time ?out|temporarily|Connection (reset|aborted|refused)",
    re.IGNORECASE,
)


class SourceTimeout(TimeoutError):
    """La fuente superó el tiempo máximo del corte."""


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 2
    backoff_s: float = 2.0
    timeout_s: float = 90.0

    @classmethod
    def from_env(cls) -> "RetryPolicy":
        return cls(
            attempts=max(1, int(os.getenv("SUPERVISION_SOURCE_ATTEMPTS", "2"))),
            backoff_s=max(0.0, float(os.getenv("SUPERVISION_RETRY_BACKOFF_S", "2"))),
            timeout_s=max(1.0, float(os.getenv("SUPERVISION_SOURCE_TIMEOUT_S", "90"))),
        )


def is_transient(error: BaseException) -> bool:
    """True si reintentar puede funcionar."""
    if isinstance(error, SourceTimeout):
        return False  # ya se esperó el máximo: reintentar duplicaría la espera
    if isinstance(error, (TimeoutError, ConnectionError)):
        return True
    return bool(_TRANSIENT.search(f"{type(error).__name__}: {error}"))


def _with_timeout(call: Callable[[], T], timeout_s: float) -> T:
    # Hilo propio: si la API se cuelga se abandona la espera (el hilo termina
    # solo cuando el cliente agota su propio timeout de red).
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call)
    try:
        return future.result(timeout=timeout_s)
    except FutureTimeout as error:
        raise SourceTimeout(f"La fuente no respondió en {timeout_s:g} s.") from error
    finally:
        executor.shutdown(wait=False)


def call_with_retry(call: Callable[[], T], policy: RetryPolicy,
                    sleep: Callable[[float], None] = time.sleep) -> tuple[T, int]:
    """Ejecuta ``call`` con tiempo máximo y reintento de errores transitorios.

    Devuelve (resultado, intentos usados). Si falla, la excepción lleva el
    atributo ``attempts`` con los intentos usados.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return _with_timeout(call, policy.timeout_s), attempt
        except Exception as error:
            if attempt >= policy.attempts or not is_transient(error):
                error.attempts = attempt  # type: ignore[attr-defined]
                raise
            sleep(policy.backoff_s * attempt)
