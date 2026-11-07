/**
 * HU-006 / HU-007 · Textos de los indicadores I1–I4 y de las reglas R1–R4.
 *
 * Las fórmulas son las del motor de TA-019 (backend/app/modulos/supervision/
 * motor_indicadores.py). Los valores no se calculan aquí: llegan ya calculados
 * (demo_supervision.js sin API; con API, de las rutas de TA-022 desde TA-040).
 */

export const INDICADORES = {
  I1: {
    etiqueta: 'Tareas completadas',
    formula: 'I1 = tareas en estado «Listo» ÷ total de tareas × 100',
    fuente: 'Notion',
  },
  I2: {
    etiqueta: 'Tareas pendientes',
    formula: 'I2 = tareas «Sin empezar» o «En curso» ÷ total de tareas × 100',
    fuente: 'Notion',
  },
  I3: {
    etiqueta: 'Tareas vencidas',
    formula: 'I3 = tareas no «Listo» con fecha límite anterior al día de corte',
    fuente: 'Notion',
  },
  I4: {
    etiqueta: 'Días sin actividad',
    formula: 'I4 = días completos entre la última evidencia (GitHub, Notion o Drive) y el corte',
    fuente: 'GitHub, Notion y Drive',
  },
}

export const REGLAS = {
  R1: { titulo: 'Tarea vencida', fuente: 'Notion' },
  R2: { titulo: 'Tarea en curso sin ediciones', fuente: 'Notion' },
  R3: { titulo: 'Repositorio sin commits', fuente: 'GitHub' },
  R4: { titulo: 'Carpeta de Drive sin cambios', fuente: 'Google Drive' },
}

const pad = n => String(n).padStart(2, '0')

/** «2026-10-13T04:59:59Z» → «13/10/2026 04:59 UTC». */
export function fechaHoraUtc(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso ?? '')
  return `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` +
    `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`
}

/** «2026-10-12T09:00:00Z» → «12/10/2026». */
export function fechaUtc(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso ?? '')
  return `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`
}

/** Formato de un valor de indicador: porcentajes con coma decimal solo si hace falta. */
export function formatoIndicador(id, valor) {
  if (valor === null || valor === undefined) return '—'
  if (id === 'I1' || id === 'I2') {
    const texto = Number.isInteger(valor) ? String(valor) : String(valor).replace('.', ',')
    return `${texto} %`
  }
  return String(valor)
}
