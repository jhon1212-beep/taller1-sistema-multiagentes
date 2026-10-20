# Módulo validacion

Dueño: Castro. Contrato publicado en AR-05 (ver `docs/sprint1/AR-05.md`).

| Archivo | Contenido |
|---|---|
| `dominio.py` | `SolicitudValidacion`, `ResultadoValidacion` (campos de la tabla `validacion`), `ValidacionInvalida` |
| `puertos.py` | Protocol `EjecutorE2E` (`ejecutar(solicitud) -> ResultadoValidacion`) |
| `adaptadores/falso.py` | `EjecutorE2EFalso`: determinista y sin red (URL con "falla" → FAIL) |

Pendiente (TA-021): el ejecutor real que dispara el workflow E2E en GitHub Actions
y registra el resultado en PostgreSQL.
