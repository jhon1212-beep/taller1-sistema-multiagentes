"""Configuración común de pytest (solo variables de entorno de prueba).

TA-030: en las pruebas las fuentes simuladas fallan a propósito; no hace falta
esperar entre reintentos (en producción la espera es de 2 s).
"""
import os

os.environ.setdefault("SUPERVISION_RETRY_BACKOFF_S", "0")

# R5: el adaptador de GitHub pide el detalle de cada commit. Las pruebas no deben
# salir a la red; las de R5 lo activan con monkeypatch y un cliente simulado.
os.environ.setdefault("GITHUB_DETALLE_COMMITS", "0")
