# -*- coding: utf-8 -*-
"""TA-006 · Adaptador real de GitHub.

Implementa el puerto FuenteEvidencia (app/modulos/evidencias/puertos.py)
reutilizando el cliente de EN-001 (cliente.py, en esta misma carpeta). Es
el reemplazo de FuenteEvidenciaFalsa una vez conectado en main.py (TA-036).
"""
from __future__ import annotations

import os

from app.modulos.evidencias.adaptadores.github.cliente import GitHubClient, GitHubError, cargar_env
from app.modulos.evidencias.referencias import repositorio_github
from app.modulos.evidencias.dominio import Evidencia, EvidenciaGitHub

LIMITE_COMMITS = 20  # Criterio de aceptación de TA-006: hasta 20 commits


def _normalizar_commit(commit_crudo: dict, proyecto_id: int, detalle: dict | None = None) -> Evidencia:
    detalle = detalle or {}
    return EvidenciaGitHub(
        fuente="github",
        id_externo=commit_crudo["sha"],
        autor=commit_crudo.get("autor") or "desconocido",
        fecha=commit_crudo.get("fecha"),
        descripcion=commit_crudo.get("mensaje") or "",
        proyecto_id=proyecto_id,
        archivos=detalle.get("archivos"),
        adiciones=detalle.get("adiciones"),
        eliminaciones=detalle.get("eliminaciones"),
        es_merge=bool(detalle.get("es_merge")),
    )


def _con_detalle() -> bool:
    """R5 necesita una consulta más por commit; GITHUB_DETALLE_COMMITS=0 la apaga."""
    return os.getenv("GITHUB_DETALLE_COMMITS", "1").strip().lower() not in ("0", "false", "no")


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
        repo = repositorio_github(referencia)
        crudos = cliente.commits_detallados(repo, desde=desde, maximo=limite)
        if not _con_detalle():
            return [_normalizar_commit(c, proyecto_id) for c in crudos]
        return [_normalizar_commit(c, proyecto_id, self._detalle(cliente, repo, c["sha"])) for c in crudos]

    @staticmethod
    def _detalle(cliente: GitHubClient, repo: str, sha: str) -> dict | None:
        # Sin detalle el commit sigue siendo evidencia; solo se omite R5 para él.
        try:
            return cliente.detalle_commit(repo, sha)
        except GitHubError:
            return None
