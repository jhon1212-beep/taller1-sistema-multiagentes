# Semana 12 · Entrega conjunta de pendientes

Este commit reúne, a pedido del equipo, lo que faltaba en `main` según la División del
Trabajo v6.0 y el Product Backlog v6.0. Lo subió Reyes; **cada dueño revisa su parte en el
PR** antes de que Mondragón lo apruebe.

Lo que sale de ejecutar algo real (URLs del despliegue, corridas de workflows, trazas de
LangSmith, sesión del piloto, horas reales) **no se inventó**: para eso quedan scripts y
plantillas que generan la evidencia al correrlos.

## Qué incluye y qué falta por integrante

### Chávez

| PBI | En este commit | Falta (lo hace Chávez) |
|---|---|---|
| SP-002 (s5) | `docs/sprint1/SP-002.md` (matriz Drive vs. Jira) y corrección de `docs/arquitectura.md` | Enlazar la página de Notion si existe |
| TA-014 (s9) | — (código ya en main) | `python backend/scripts/sincronizar_drive.py` + captura de la consulta de las 10 evidencias |
| TA-038 (s9) | `evidencias/TA-038_pytest.txt` (9 pruebas en verde) | — |
| RN-002 (s10) | `evidencias/RN-002_pytest.txt` (8 pruebas de fallo en verde) | — |
| TA-033 (s10) | — | 2 ejecuciones de «Corte diario» en Actions + captura |
| TA-025 (s11) | `render.yaml`, `frontend/vercel.json`, `backend/scripts/ta025_medir_arranque.py` | Desplegar; correr el script; «E2E contra produccion» con las URLs |
| TA-029 (s11) | `docs/sprint2/TA-029_Registro_proyectos_piloto.md`, `backend/scripts/ta029_verificar_fuentes.py` | Autorizaciones, verificación y registro de los 2 proyectos |
| DO-007 (s12) | `docs/tecnica.md`, sección 2 | Revisar y agregar capturas del despliegue |
| DO-004 (s12) | `docs/sprint2/DO-004_Informe_piloto_plantilla.md` | Completar después del piloto y exportar a PDF |
| TA-034 (s12) | — | Solo si el piloto o TA-027 abren defectos del módulo evidencias |

### Reyes

| PBI | En este commit | Falta |
|---|---|---|
| TA-046, RN-003, TA-045, TA-026 (s11) | Código, pruebas y `Semana11_Reyes_…md` | Capturas de LangSmith, checklist contra Neon, evidencia de TA-037 |
| TA-030 (s12) | `supervision/estabilidad.py`, pruebas, `ta030_tres_ejecuciones.py` | Correr las 3 ejecuciones con claves reales |
| DO-005 (s12) | `docs/tecnica.md`, sección 1 | — |
| Drive opcional | Backend, frontend, pruebas y capturas | — |

### Mondragón

| PBI | En este commit | Falta |
|---|---|---|
| DO-006 (s12) | `docs/sprint2/DO-006_Guia_docente.md` y `.pdf` | Revisar textos y capturas; reemplazar por capturas de producción si quiere |
| Pantallas con Drive opcional | Formulario, Detalle, Dashboard y Mis proyectos | Revisar en el PR |
| TA-031, TA-050 (s12) | — | Ajustes previos al piloto y notas de observación en Notion |

### Castro

| PBI | En este commit | Falta |
|---|---|---|
| TA-051 (s12) | `docs/sprint2/TA-051_Tabulacion_piloto.xlsx` (vacía, con fórmulas SUS y criterios de TA-028) | Llenar después del piloto |
| TA-052 (s12) | `scripts/ta052_regresion_final.ps1` | Correrlo antes y después del piloto |
| TA-032 (s12) | — | Sesión del piloto |
| TA-027 | — | Repetir CP-API1 a CP-API6 contra producción cuando exista TA-025 |

## Otros cambios

- Se borró `archivo_temporal.txt` (vacío) y el enlace de Figma de la raíz pasó a `docs/sprint1/TA-002_enlace_figma.txt`.
- `tests/conftest.py` pone en 0 la espera entre reintentos solo en las pruebas.
