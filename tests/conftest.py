"""Configuración común de pytest.

TA-030: en las pruebas las fuentes simuladas fallan a propósito; no hace falta
esperar entre reintentos (en producción la espera es de 2 s).
"""
import os

os.environ.setdefault("SUPERVISION_RETRY_BACKOFF_S", "0")
