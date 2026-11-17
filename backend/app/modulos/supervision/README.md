# Módulo supervision

Dueño: Reyes. Núcleo multiagente del sistema: grafo de agentes, motor de
indicadores y reglas, alertas explicables, historial por corte y API de consulta.

## Grafo (TA-015, TA-023)

`START -> supervisor -> [github_agent | notion_agent | drive_agent] -> consolidate -> evaluate -> explain -> END`

- `supervisor`: valida las referencias de las fuentes y la fecha de corte.
- `github_agent`, `notion_agent`, `drive_agent`: corren en paralelo (`Send`), obtienen evidencias y registran su fallo sin detener a los demás (RN-002). Desde TA-030 reintentan una vez los errores transitorios (5xx, 429, red) y cortan por tiempo una fuente colgada (`estabilidad.py`).
- `consolidate`: une las evidencias y elimina duplicados por fuente e identificador.
- `evaluate`: ejecuta `motor_indicadores.evaluar`, sin LLM, para I1–I4 y R1–R4.
- `explain`: arma un contexto seudonimizado y pide **todas** las explicaciones del corte en una sola solicitud (TA-046, `explicacion.py`); si falla, la plantilla explica todas.

### Drive opcional

GitHub y Notion son obligatorias; Drive no. Si el proyecto no registró la carpeta,
el Supervisor no despacha al agente Drive y marca la fuente `no_configurada`
(no es un `fallo` y no lleva error). El nodo `evaluate` descarta las alertas de
esa fuente, así que R4 no se emite. I1–I3 salen de Notion y no cambian; I4 usa la
última evidencia de las fuentes registradas. Lo cubre `tests/integration/test_drive_opcional.py`.

### Estabilidad con fuentes reales (TA-030)

| Variable | Por defecto | Qué controla |
|---|---|---|
| `SUPERVISION_SOURCE_ATTEMPTS` | 2 | Intentos por fuente (solo se reintentan errores transitorios) |
| `SUPERVISION_RETRY_BACKOFF_S` | 2 | Segundos de espera antes de reintentar |
| `SUPERVISION_SOURCE_TIMEOUT_S` | 90 | Tiempo máximo por fuente; pasado, la fuente queda en `fallo` |

Las credenciales inválidas, los permisos y las referencias mal escritas no se
reintentan. El consolidado trae `estabilidad`: intentos y duración de cada agente.
Evidencia: `python backend/scripts/ta030_tres_ejecuciones.py` (3 ejecuciones con trazas `TA-030`).

## Arquitectura hexagonal

| Capa | Archivos |
|---|---|
| Dominio | `dominio.py` (tipos y regla de día de corte), `grafo/estado.py`, `motor.py`, `motor_indicadores.py`, `pseudonymizer.py` |
| Puertos (AR-02) | `puertos.py`: `GeneradorExplicacion`, `RepositorioSupervision` y `RepositorioCortes` (consultas de TA-018/TA-022) |
| Adaptadores | `adaptadores/plantilla.py`, `gemini.py`, `resilient.py`, `memoria.py`, `sql.py` |
| Caso de uso | `service.py` (`SupervisionService`): solo conoce los puertos |
| Entrada HTTP | `rutas.py`: arma el servicio con `SqlSupervisionRepository` y traduce HTTP |
| Configuración | `sources.py`: elige fuentes (`dataset` o `real`) y explicador (`template` o `gemini`) por variables de entorno |

## Indicadores y reglas (Product Backlog v6.0)

| Id | Definición |
|---|---|
| I1 | Tareas `Listo` ÷ total × 100 |
| I2 | Tareas `Sin empezar` o `En curso` ÷ total × 100 |
| I3 | Tareas no `Listo` con fecha límite anterior al día de corte |
| I4 | Días entre la última evidencia (GitHub, Notion o Drive) y el corte |
| R1–R4 | Tarea vencida, tarea estancada (más de 7 días), repositorio sin commits en 7 días, Drive sin cambios en 14 días |

`motor.py` (TA-019) y `motor_indicadores.py` (TA-023) dan los mismos valores;
lo comprueban `test_motor_reglas.py` y `test_i2_coincide_con_el_dataset`.

## Historial y API (TA-018, TA-022)

- Un corte por proyecto y día en hora de Lima. Repetir el mismo día lo reemplaza.
- Todo el corte se guarda en una transacción, y cada alerta apunta a su evidencia (RN-003).

| Ruta | Qué hace |
|---|---|
| `POST /proyectos/{id}/consolidacion` | Ejecuta el grafo y guarda el corte (`fecha_corte` opcional, ISO 8601 con zona) |
| `GET /proyectos/{id}/indicadores` | I1–I4 y estado de las fuentes (`?fecha_corte=AAAA-MM-DD`; sin ella, el último corte) |
| `GET /proyectos/{id}/alertas` | Alertas R1–R4 del corte, cada una con su evidencia de origen |
| `GET /proyectos/{id}/historial` | Todos los cortes: I1–I4, alertas por regla y CP-17 del día |

Las 4 rutas exigen JWT (401 sin token) y devuelven 404 si el proyecto es de otro docente.
`backend/scripts/ejecutar_corte.py` las usa desde `.github/workflows/corte.yml` (TA-033).

## Ejecutar

```powershell
# Grafo por consola (TA-015/TA-023)
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer template
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer gemini
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer gemini-429

# Corte por la API (TA-022), con la API levantada
$env:CORTE_CORREO="docente@..."; $env:CORTE_CLAVE="..."
python backend/scripts/ejecutar_corte.py

# Métricas de viabilidad (semana 10)
python backend/scripts/measure_supervision_metrics.py
```

Variables: `SUPERVISION_SOURCES` (`dataset` | `real`), `SUPERVISION_EXPLAINER`
(`template` | `gemini`), `GEMINI_API_KEY`, `GEMINI_MODEL` y las de LangSmith.
Con `real`, las referencias de las fuentes pueden ser los enlaces del formulario:
`evidencias/referencias.py` extrae `org/repo`, el id de la base de Notion y el de la carpeta de Drive.
Las fuentes pueden ser de cualquier equipo; ver `docs/sprint2/Conectar_fuentes_de_otro_equipo.md`.

## Pruebas

```powershell
python -m pytest -q
python -m pytest tests/unit/test_motor_reglas.py tests/unit/test_pseudonymizer.py tests/unit/test_explanation_generators.py -v
python -m pytest tests/integration/test_explainable_alerts.py tests/integration/test_ta018_cutoff_history.py tests/integration/test_ta022_supervision_api.py -v
python -m pytest tests/integration/test_ta037_cp10_real_sources.py -v -rs   # CP-10; la parte real necesita credenciales
```

Las pruebas de TA-018 y TA-022 necesitan `DATABASE_URL` con una base migrada. Sin ella se omiten.

## Seguridad

- No se imprimen claves de API.
- El prompt incluye solo campos seleccionados, con los autores cambiados por `Member N`.
- La protección cubre los nombres de autores conocidos. Para usar otros datos reales hace falta un control de privacidad más amplio.

## Contrato y trazabilidad (TA-045, RN-003)

- Modelos de respuesta de las 4 rutas: `contrato.py`. Contrato completo: `docs/api/openapi.json` (`python backend/scripts/exportar_openapi.py`).
- Checklist de trazabilidad contra la base: `python backend/scripts/verificar_trazabilidad.py` (consultas en `docs/sprint2/RN-003_trazabilidad.sql`).
