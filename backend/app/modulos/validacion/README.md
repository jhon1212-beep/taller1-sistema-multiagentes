# Módulo validacion

Dueño: Castro. Contrato publicado en AR-05 (ver `docs/sprint1/AR-05.md`).

| Archivo | Contenido |
|---|---|
| `dominio.py` | `SolicitudValidacion`, `ResultadoValidacion` (campos de la tabla `validacion`), `ValidacionInvalida` |
| `puertos.py` | Protocol `EjecutorE2E` (`ejecutar(solicitud) -> ResultadoValidacion`) |
| `adaptadores/falso.py` | `EjecutorE2EFalso`: determinista y sin red (URL con "falla" → FAIL) |

## TA-021 / TA-047 (semana 9)

| Archivo | Contenido |
|---|---|
| `servicio.py` | `AgenteValidacion`: ejecuta la validación y la registra |
| `rutas.py` | `POST /validaciones` (disparo por API; ejecutor según `E2E_EJECUTOR`) |
| `adaptadores/github_actions.py` | Dispara `e2e.yml`, localiza el run por código de correlación y lee su conclusión |
| `adaptadores/local.py` | Corre `e2e/validar-url.mjs` sin GitHub Actions (`run_id_actions` negativo) |
| `adaptadores/sql.py` | Inserta en la tabla `validacion` |

Un FAIL funcional se registra como resultado; un fallo de infraestructura lanza `ErrorInfraestructuraValidacion` y no se registra.

Pendiente: repositorio de consultas (TA-048).
