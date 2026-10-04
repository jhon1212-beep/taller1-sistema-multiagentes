# -*- coding: utf-8 -*-
"""TA-006 · Adaptador real de GitHub.

Implementa el puerto FuenteEvidencia (app/modulos/evidencias/puertos.py)
reutilizando el cliente de EN-001 (cliente.py, en esta misma carpeta). Es
el reemplazo de FuenteEvidenciaFalsa una vez conectado en main.py (TA-036).
"""
from __future__ import annotations

from app.modulos.evidencias.adaptadores.github.cliente import GitHubClient, cargar_env
from app.modulos.evidencias.dominio import Evidencia

LIMITE_COMMITS = 20  # Criterio de aceptación de TA-006: hasta 20 commits


def _normalizar_commit(commit_crudo: dict, proyecto_id: int) -> Evidencia:
    return Evidencia(
        fuente="github",
        id_externo=commit_crudo["sha"],
        autor=commit_crudo.get("autor") or "desconocido",
        fecha=commit_crudo.get("fecha"),
        descripcion=commit_crudo.get("mensaje") or "",
        proyecto_id=proyecto_id,
    )


class FuenteEvidenciaGitHub:
    """Implementación real del puerto FuenteEvidencia para GitHub.

    Puede lanzar GitHubError / RateLimitError (ver cliente.py); quien la
    use decide cómo manejarlo (ver agentes/agente_github.py).
    """

    def obtener_evidencias(
        self,
        referencia: str,
        proyecto_id: int,
        *,
        limite: int | None = LIMITE_COMMITS,
        desde: str | None = None,
    ) -> list[Evidencia]:
        env = cargar_env()
        cliente = GitHubClient(token=env.get("GITHUB_TOKEN"), org=env.get("GITHUB_ORG"))
        crudos = cliente.commits_detallados(referencia, desde=desde, maximo=limite)
        return [_normalizar_commit(c, proyecto_id) for c in crudos]
