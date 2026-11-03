# -*- coding: utf-8 -*-
"""TA-048 · Repositorio de validaciones en memoria (sin base de datos).

Cumple el puerto RepositorioValidaciones. Sirve para probar el módulo y las rutas
sin PostgreSQL, igual que los repositorios en memoria de proyectos y autenticación.
"""
from __future__ import annotations

from app.modulos.validacion.dominio import ResultadoValidacion, ValidacionGuardada
from app.modulos.validacion.revision import validar_consulta


class RepositorioValidacionesMemoria:
    def __init__(self) -> None:
        self._filas: list[ValidacionGuardada] = []

    def registrar(self, resultado: ResultadoValidacion) -> int:
        fila = ValidacionGuardada(id=len(self._filas) + 1, resultado=resultado)
        self._filas.append(fila)
        return fila.id

    def _del_proyecto(self, proyecto_id: int) -> list[ValidacionGuardada]:
        propias = [f for f in self._filas if f.resultado.proyecto_id == proyecto_id]
        return sorted(propias, key=lambda f: (f.resultado.ejecutada_en, f.id), reverse=True)

    def ultima(self, proyecto_id: int) -> ValidacionGuardada | None:
        filas = self._del_proyecto(proyecto_id)
        return filas[0] if filas else None

    def listar(
        self, proyecto_id: int, *, resultado: str | None = None, limite: int = 20
    ) -> list[ValidacionGuardada]:
        validar_consulta(resultado, limite)
        filas = self._del_proyecto(proyecto_id)
        if resultado:
            filas = [f for f in filas if f.resultado.resultado == resultado]
        return filas[:limite]

    def contar(self, proyecto_id: int) -> dict[str, int]:
        filas = self._del_proyecto(proyecto_id)
        return {r: sum(1 for f in filas if f.resultado.resultado == r) for r in ("PASS", "FAIL")}
