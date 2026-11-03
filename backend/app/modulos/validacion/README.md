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

## TA-048 / HU-008 (semana 10)

| Archivo | Contenido |
|---|---|
| `puertos.py` | Protocol `RepositorioValidaciones`: `registrar`, `ultima`, `listar` (filtro por resultado y límite) y `contar` |
| `dominio.py` | `ValidacionGuardada` (id + resultado) |
| `adaptadores/sql.py` | `RepositorioValidacionesSQL` (`RegistroValidacionSQL` sigue existiendo como alias) |
| `adaptadores/memoria.py` | `RepositorioValidacionesMemoria`: mismo contrato, sin base de datos |
| `revision.py` | Reglas de `resultado` y `limite` comunes a los repositorios |
| `rutas.py` | `GET /proyectos/{id}/validaciones` (historial y recuento) y `GET /proyectos/{id}/validaciones/ultima` |

Las dos rutas exigen sesión y solo devuelven proyectos del docente (404 si no es suyo). La más reciente va primero. `ultima` da 404 si el proyecto nunca se validó; el historial de un proyecto sin validaciones es una lista vacía con recuento en cero.

Pruebas: `tests/unit/test_validaciones_repositorio.py` (mismo contrato sobre memoria y SQL/SQLite), `tests/test_validaciones_consulta.py` (rutas con login real), `tests/test_validacion_postgres.py` (PostgreSQL, se omite sin `DATABASE_URL`) y `e2e/consulta-validaciones.spec.js` (Playwright contra la API real).

## TA-049 (semana 10)

`tests/integration/test_cp12_cp19.py` automatiza CP-12 a CP-19, uno por caso y con el CP en el nombre. El CI los ejecuta en el job `integracion-cp` y escribe una tabla por CP en el resumen (`tests/resumen_cp.py`).
