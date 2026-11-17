# Semana 11 · TA-046, RN-003, TA-045 y TA-026

**Responsable:** Reyes · **Sprint:** 2 · **Semana:** 11 (09/11 – 13/11/2026) · **Verificador:** Castro

## Resumen

Las explicaciones de un corte salen ahora en **una sola solicitud a Gemini** en vez de una por alerta (TA-046). La trazabilidad de alertas y validaciones queda comprobada con un checklist que se genera desde la base (RN-003). Las rutas de supervisión publican su forma de respuesta en el contrato OpenAPI (TA-045). TA-026 cierra el ISS-02 de TA-027 con la evidencia de CP-10.

## TA-046 · Agrupar llamadas a Gemini por proyecto

| Pieza | Archivo | Cambio |
|---|---|---|
| Puerto | `backend/app/modulos/supervision/puertos.py` | `GeneradorExplicacionLote.generar_lote(alertas, fecha_corte, contextos)` |
| Gemini | `backend/app/modulos/supervision/adaptadores/gemini.py` | `build_batch_prompt` arma un prompt con todas las alertas seudonimizadas; `parse_batch_answer` exige un arreglo JSON con un texto por alerta, en orden |
| Respaldo | `backend/app/modulos/supervision/adaptadores/resilient.py` | Si la solicitud falla (429, JSON inválido o número de textos distinto), la plantilla explica todas y se registra un respaldo por alerta |
| Plantilla | `backend/app/modulos/supervision/adaptadores/plantilla.py` | `generar_lote` sin LLM |
| Grafo | `backend/app/modulos/supervision/grafo/supervisor.py` + `explicacion.py` | El nodo `explain` hace una sola llamada por corte; un generador sin `generar_lote` sigue funcionando alerta por alerta |
| Razonamiento | `gemini.py` | `GEMINI_THINKING_BUDGET` (por ejemplo `0`) o `GEMINI_REASONING_EFFORT` (`low`) reducen el razonamiento del modelo; solo se envían si están definidas |

| Criterio | Evidencia | Estado |
|---|---|---|
| 1) 1 llamada por proyecto y corte, verificado en LangSmith | `tests/unit/test_ta046_gemini_por_lote.py`; capturas `evidencias/TA-046_antes_langsmith.png` y `TA-046_despues_langsmith.png` | Código y pruebas listos; capturas pendientes |
| 2) Razonamiento del modelo reducido | `GEMINI_THINKING_BUDGET=0`; tokens antes/después en las mismas capturas | Pendiente de medir con Gemini real |
| 3) Los 4 escenarios de TA-023 siguen en verde | `tests/integration/test_explainable_alerts.py` (CP-12 a CP-15, sin nombres reales, CP-19) | Cumple |

Con el dataset, el corte del proyecto 2 pasa de **7 solicitudes a 1**, y el del proyecto 1 de 6 a 1. Con el límite gratuito de 20 solicitudes diarias, eso permite hasta 20 cortes al día en vez de 2 o 3.

Se ajustaron dos pruebas que contaban una solicitud por alerta: `test_no_real_name_is_sent_to_gemini` (TA-023) y `test_cp16_el_prompt_de_gemini_no_lleva_nombres_reales` (TA-049, Castro). Ambas siguen comprobando que no se envían nombres reales.

## RN-003 · Trazabilidad de resultados

| Criterio | Cómo se garantiza | Cómo se comprueba |
|---|---|---|
| 1) 100 % de las alertas guarda el id de su evidencia | `alerta.evidencia_id` es una clave foránea obligatoria; `SqlSupervisionRepository.guardar` no inserta una alerta sin evidencia y la cuenta en `alertas_sin_evidencia` | `backend/scripts/verificar_trazabilidad.py` y `docs/sprint2/RN-003_trazabilidad.sql` (consultas 1 a 3) |
| 2) 100 % de las validaciones guarda el id de su ejecución en GitHub Actions | `validacion.run_id_actions` es obligatorio y el dominio rechaza un resultado sin él | Mismo script, consulta 4 |

Evidencia: `evidencias/RN-003_checklist.md`, generado contra la base de Neon del equipo.

## TA-045 · Ajustes de contrato para el frontend

| Ajuste | Pedido por | Commit |
|---|---|---|
| `GET /alertas` devuelve la evidencia de origen de cada alerta (campo `evidencia`) para el detalle de alerta | Pantalla de detalle (TA-040) | `1d28db4` (PR #33) |
| Las fuentes aceptan los enlaces del formulario | Registro de proyectos (HU-002) | `1d28db4` (PR #33) |
| Las 4 rutas de supervisión declaran su modelo de respuesta | Contrato OpenAPI (TA-045) | Este PR |

- Modelos: `backend/app/modulos/supervision/contrato.py`. Usan `extra="allow"`, así que no se pierde ningún campo que ya devolvía la API.
- Contrato: `docs/api/openapi.json`, que se regenera con `python backend/scripts/exportar_openapi.py`.
- La prueba `tests/unit/test_ta045_contrato_openapi.py` falla si una ruta cambia y el contrato no se regenera.

En su informe de la semana 11, Mondragón no registró ajustes pendientes para el backend.

## TA-026 · Corrección de defectos críticos del núcleo

TA-027 (Castro) no encontró defectos críticos: «No se encontraron defectos nuevos en el código del producto». Estado de sus issues en lo que toca al núcleo:

| Issue | Severidad | Resolución |
|---|---|---|
| ISS-02 · CP-10 con las 3 fuentes reales no se ejecutó | Media | **Cerrado.** CP-10 en verde con GitHub, Notion y Drive reales (`tests/integration/test_ta037_cp10_real_sources.py`, 2 de 2). Evidencia en `evidencias/TA-037_cp10_consolidado.json` y `TA-037_traza_langsmith.png` |
| ISS-04 · CP-09, CP-16 y CP-18 sin definición escrita | Media | Justificado: CP-16 (fallo de GitHub, RN-002) y CP-18 (Historial frente a PostgreSQL, HU-009) están cubiertos por TA-049 y TA-018; el equipo confirma la asignación |
| ISS-01, ISS-03, ISS-05, ISS-06 | Baja o informativa | Fuera del núcleo (entorno, despliegue, Sprint 1 y comportamiento diseñado) |

## Verificación

| Prueba | Resultado |
|---|---|
| Backend como en el CI (Python 3.12, sin base de datos) | 323 aprobadas, 19 omitidas |
| CP-12 a CP-19 | 8 de 8 |
| Backend con PostgreSQL 16 | 335 aprobadas, 7 omitidas |
| Frontend: E2E del modo demo | 18 de 18 |
| Frontend contra la API real | 5 de 5 |

## Horas reales

Registrar solo el tiempo efectivamente trabajado.

| PBI | Estimado | Real (h) |
|---|---:|---:|
| TA-046 | 3,0 h (0,75 SP) | Pendiente |
| RN-003 | 2,0 h (0,5 SP) | Pendiente |
| TA-045 | 2,0 h (0,5 SP) | Pendiente |
| TA-026 | 2,0 h (0,5 SP) | Pendiente |
