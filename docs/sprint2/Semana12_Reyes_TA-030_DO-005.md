# Semana 12 · TA-030 y DO-005 (+ Drive opcional)

**Responsable:** Reyes · **Sprint:** 2 · **Semana:** 12 (16/11 – 20/11/2026) · **Verificador:** Chávez (Scrum Master)

## Resumen

Los agentes de fuente reintentan los errores pasajeros de las APIs reales y no se quedan
esperando a una fuente colgada (TA-030). La documentación técnica del sistema multiagente
queda en `docs/tecnica.md` (DO-005). Además, a pedido del equipo, **Google Drive pasa a
ser una fuente opcional** del proyecto.

## TA-030 · Ajustes de estabilidad con datos reales

| Ajuste | Archivo | Por qué |
|---|---|---|
| Reintento de errores transitorios (5xx, 429, red, tiempo agotado) | `supervision/estabilidad.py` | Un 502 aislado de GitHub dejaba la fuente en `fallo` todo el corte |
| Sin reintento para credenciales, permisos o referencias inválidas | `estabilidad.is_transient` | Reintentar no los arregla y solo alarga el corte |
| Tiempo máximo por fuente (90 s; 60 s en `render.yaml`) | `estabilidad.call_with_retry` | Una API colgada no deja esperando al docente; las demás fuentes siguen |
| Medición por agente: intentos y duración | `grafo/supervisor.py` → `estabilidad` en el consolidado | Insumo de las 3 ejecuciones y de la traza |
| Variables `SUPERVISION_SOURCE_ATTEMPTS`, `SUPERVISION_RETRY_BACKOFF_S`, `SUPERVISION_SOURCE_TIMEOUT_S` | `.env.example`, `render.yaml` | Ajustables sin tocar código |

Se probó también el caso de dos guardados simultáneos del mismo corte (`corte.yml` y el
botón del docente): el repositorio actual no duplica alertas, así que no hizo falta un
bloqueo adicional. La prueba queda como regresión.

| Criterio | Evidencia | Estado |
|---|---|---|
| Ajustes con commits | Este commit; `tests/unit/test_ta030_estabilidad.py` (18 pruebas) | Cumple |
| Trazas de 3 ejecuciones en LangSmith | `python backend/scripts/ta030_tres_ejecuciones.py --github <url> --notion <url> [--drive <url>]` → `evidencias/TA-030_ejecuciones.json` y `.md` + captura `evidencias/TA-030_langsmith.png` (filtro tag `TA-030`) | Pendiente: necesita las claves reales |

## Drive opcional

| Capa | Cambio |
|---|---|
| Proyectos (HU-002) | `FUENTES_OBLIGATORIAS = github, notion`; `drive` acepta vacío o `null` al registrar y al editar |
| Supervisor | Sin carpeta: estado `no_configurada` (no es `fallo`), no se despacha el agente y no se evalúa R4 |
| Repositorio y rutas | `/indicadores` y `/documentos` informan `no_configurada` |
| Frontend | Campo «Carpeta de Google Drive (opcional)»; tarjeta «No configurada»; «2 de 2 disponibles»; aviso en la pestaña Drive |
| Pruebas | `tests/integration/test_drive_opcional.py` (5), `tests/test_proyectos.py` (2 nuevas), CP-API6 en `frontend/e2e-api/conectado.spec.js` |

Evidencia: `evidencias/semana12/drive_opcional_01_dashboard.png`, `_02_pestana_drive.png` y
`_03_registro.png` (generadas con la API local y el dataset de TA-017). Con el mismo
dataset, quitar Drive deja I1–I4 iguales (40 %, 60 %, 4, 0) y las 6 alertas R1–R2.

## R5 · Coherencia entre commit y código (pedido del docente)

Alcance nuevo solicitado por el docente: avisar cuando el mensaje de un commit no
corresponde a lo que el commit cambió, con su justificación y un botón al commit.

| Capa | Cambio |
|---|---|
| Agente GitHub | `cliente.detalle_commit`: archivos, líneas y si es merge (`GET /commits/{sha}`). Si falla, el commit sigue siendo evidencia y solo se omite R5. `GITHUB_DETALLE_COMMITS=0` lo apaga |
| Dominio | `EvidenciaGitHub` (archivos, adiciones, eliminaciones, es_merge); no se guarda en la base |
| Regla | `supervision/coherencia.py` (determinista, sin LLM) y R5 en `motor_indicadores.py` para los commits de los 7 días previos al corte |
| Explicación | El motivo va en el prompt (seudonimizado) y el grafo garantiza que aparezca en la explicación |
| Base | Migración `0002`: `alerta.regla` admite R5 |
| Frontend | Filtro R5, título «Commit a revisar», aviso de que no prueba una mentira y botón al commit |

Validación sobre el historial real del repositorio: de 236 commits (todas las ramas),
la primera versión marcaba 9; tras excluir «plan/informe de pruebas» y aceptar rutas
con «prueba/test», marca 3, los tres incoherencias reales (dos «Delete X» que en
realidad agregaron 10 archivos y un commit vacío).

Pruebas: `tests/unit/test_r5_coherencia_commits.py` (30) y CP-API8.
Evidencia: `evidencias/semana12/r5_alerta_commit.png`.

## DO-005 · Documentación técnica del sistema multiagente

`docs/tecnica.md`, sección 1: grafo con diagrama, nodos, indicadores y reglas, fuentes
opcionales, Gemini por lote y privacidad, estabilidad, arquitectura hexagonal del módulo,
API y pruebas. La sección 2 (DO-007) es de Chávez.

## Verificación

| Suite | Resultado |
|---|---|
| `pytest` sin base | 347 pasan, 21 omitidas |
| `pytest` con PostgreSQL | 361 pasan, 7 omitidas (fuentes reales y Gemini real) |
| Playwright demo | 18 de 18 |
| Playwright con API local | 6 de 6 (CP-API1 a CP-API6) |

## Horas

| PBI | Estimadas | Reales |
|---|---|---|
| TA-030 | 5 h | Pendiente |
| DO-005 | 4 h | Pendiente |
| Ceremonias | 1 h | Pendiente |
