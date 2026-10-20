# -*- coding: utf-8 -*-
"""HU-001 · Servicio de autenticación real: bcrypt para la clave y JWT para la sesión.

Implementa el puerto ServicioAutenticacion (AR-04). El token es un JWT HS256
firmado con un secreto que llega por configuración (nunca escrito en el código).

Limitación conocida: la lista de sesiones cerradas vive en memoria del proceso;
con varias instancias del servidor o tras un reinicio, un token cerrado seguiría
vigente hasta su expiración. Para el MVP (una instancia, sesiones de 8 h) basta.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

import bcrypt
import jwt

from app.modulos.autenticacion.dominio import (
    CredencialesInvalidas,
    Docente,
    Sesion,
    SesionInvalida,
)
from app.modulos.autenticacion.puertos import RepositorioDocentes

DURACION_SESION = timedelta(hours=8)
ALGORITMO = "HS256"
LONGITUD_MINIMA_SECRETO = 32

# Hash de una clave descartable: se verifica aunque el correo no exista, para no
# distinguir "correo inexistente" de "clave incorrecta" por el tiempo de respuesta.
_HASH_RELLENO = bcrypt.hashpw(b"relleno-sin-uso", bcrypt.gensalt(rounds=12)).decode("ascii")


def hashear_password(password: str, *, rondas: int = 12) -> str:
    """bcrypt, como exige docente.password_hash en el modelo de datos."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rondas)).decode("ascii")


class ServicioAutenticacionReal:
    def __init__(
        self,
        repositorio: RepositorioDocentes,
        secreto: str,
        *,
        ahora: Callable[[], datetime] | None = None,
        duracion: timedelta = DURACION_SESION,
        sesiones_cerradas: set[str] | None = None,
    ) -> None:
        if len(secreto) < LONGITUD_MINIMA_SECRETO:
            raise ValueError(
                f"El secreto JWT debe tener al menos {LONGITUD_MINIMA_SECRETO} caracteres."
            )
        self._repo = repositorio
        self._secreto = secreto
        self._ahora = ahora or (lambda: datetime.now(timezone.utc))
        self._duracion = duracion
        # Compartido entre instancias del servicio (una por petición HTTP).
        self._cerradas = sesiones_cerradas if sesiones_cerradas is not None else set()

    def iniciar_sesion(self, correo: str, password: str) -> Sesion:
        encontrado = self._repo.buscar_por_correo(correo)
        docente, hash_guardado = encontrado if encontrado else (None, _HASH_RELLENO)
        clave_ok = bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("ascii"))
        if docente is None or not docente.activo or not clave_ok:
            raise CredencialesInvalidas("Correo o contraseña incorrectos.")
        emitida = self._ahora()
        expira = emitida + self._duracion
        token = jwt.encode(
            {
                "sub": str(docente.id),
                "iat": int(emitida.timestamp()),
                "exp": int(expira.timestamp()),
                "jti": secrets.token_urlsafe(8),
            },
            self._secreto,
            algorithm=ALGORITMO,
        )
        return Sesion(token=token, docente_id=docente.id, emitida_en=emitida, expira_en=expira)

    def _leer(self, token: str) -> dict:
        try:
            # La expiración se valida abajo contra el reloj inyectado, no el del sistema.
            return jwt.decode(
                token, self._secreto, algorithms=[ALGORITMO], options={"verify_exp": False}
            )
        except jwt.PyJWTError as error:
            raise SesionInvalida("Token inválido.") from error

    def obtener_docente(self, token: str) -> Docente:
        datos = self._leer(token)
        if self._ahora().timestamp() >= datos["exp"]:
            raise SesionInvalida("La sesión expiró.")
        if datos["jti"] in self._cerradas:
            raise SesionInvalida("Sesión inexistente o cerrada.")
        docente = self._repo.obtener(int(datos["sub"]))
        if docente is None or not docente.activo:
            raise SesionInvalida("El docente de la sesión ya no existe o fue desactivado.")
        return docente

    def cerrar_sesion(self, token: str) -> None:
        try:
            self._cerradas.add(self._leer(token)["jti"])
        except SesionInvalida:
            pass  # cerrar una sesión inexistente no es un error
