/**
 * TA-040 · Traduce las respuestas de supervisión de la API (TA-022) a la forma
 * que ya usan las vistas con los datos de demostración, para reutilizar las
 * mismas tarjetas, filtros y fichas de evidencia.
 *
 * API (GET /proyectos/{id}/alertas):
 *   { regla, fuente, evidencia_ids, explicacion, origen_explicacion,
 *     evidencia: { fuente, id_externo, autor, fecha, descripcion, estado?, fecha_limite?, tipo_archivo? } }
 * Vistas (demo_supervision.js):
 *   { id, regla, fuente, explicacion, origen_explicacion,
 *     evidencia: { tipo, id, titulo, responsable, fecha, estado?, fecha_limite?, sha?, tipo_archivo? } }
 */

const TIPO_POR_FUENTE = { notion: 'tarea', github: 'commit', drive: 'documento' }

/** Alerta de la API → alerta de las vistas (con la fecha de corte del día consultado). */
export function alertaDeApi(a, fechaCorte, proyecto) {
  const idEvidencia = a.evidencia?.id_externo ?? a.evidencia_ids?.[0] ?? ''
  const ev = a.evidencia ?? {}
  const evidencia = {
    tipo: TIPO_POR_FUENTE[a.fuente] ?? 'documento',
    id: idEvidencia,
    titulo: ev.descripcion ?? `Evidencia ${idEvidencia}`,
    responsable: ev.autor ?? null,
    fecha: ev.fecha ?? null,
    estado: ev.estado ?? null,
    fecha_limite: ev.fecha_limite ?? null,
    tipo_archivo: ev.tipo_archivo ?? null,
    sha: a.fuente === 'github' ? idEvidencia.slice(0, 7) : undefined,
    enlace: enlaceEvidencia(a.fuente, idEvidencia, proyecto),
  }
  return {
    id: `${a.regla}-${a.fuente}-${idEvidencia}`,
    regla: a.regla,
    fuente: a.fuente,
    explicacion: a.explicacion,
    origen_explicacion: a.origen_explicacion,
    fecha_corte: fechaCorte,
    evidencia,
  }
}

/** «https://github.com/org/repo(.git)» u «org/repo» → URL del repositorio; si no, null. */
function urlRepositorio(referencia) {
  const ref = String(referencia ?? '').trim()
  if (/^https?:\/\/github\.com\/[^/]+\/[^/]+/i.test(ref)) {
    return ref.replace(/\.git$/, '').replace(/\/+$/, '').split('/').slice(0, 5).join('/')
  }
  if (/^[\w.-]+\/[\w.-]+$/.test(ref)) return `https://github.com/${ref}`
  return null
}

/**
 * HU-007 · «Evidencia enlazada»: enlace al registro original en su fuente.
 * Las evidencias del dataset de demostración (ids «tarea-p1-09», «archivo-p2-06»…)
 * no existen fuera del sistema y no llevan enlace.
 */
export function enlaceEvidencia(fuente, id, proyecto) {
  if (!id || /^(tarea|commit|archivo)-p\d+-/.test(id)) return null
  if (fuente === 'github') {
    const repo = urlRepositorio(proyecto?.github)
    return repo && /^[0-9a-f]{7,40}$/i.test(id) ? `${repo}/commit/${id}` : null
  }
  if (fuente === 'notion') return `https://www.notion.so/${id.replace(/-/g, '')}`
  if (fuente === 'drive') return `https://drive.google.com/file/d/${id}/view`
  return null
}

/**
 * Fecha de corte para POST /consolidacion: fin del día elegido en hora de Lima,
 * igual que el valor por defecto del backend («AAAA-MM-DDT23:59:59-05:00»).
 */
export const corteFinDeDia = dia => `${dia}T23:59:59-05:00`

/** Hoy en Lima como «AAAA-MM-DD» (valor inicial del selector de fecha de corte). */
export function hoyEnLima() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Lima', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}

/** «2026-10-12» → «12/10/2026» (las rutas GET devuelven solo el día del corte). */
export function diaCorte(dia) {
  const [a, m, d] = String(dia ?? '').slice(0, 10).split('-')
  return a && m && d ? `${d}/${m}/${a}` : String(dia ?? '')
}

/** Texto de la fecha de corte tal como la guarda el backend: fin del día en Lima. */
export const textoCorte = dia => `${diaCorte(dia)} · 23:59 (hora de Lima)`

/** Estado de una fuente según el backend: ok | fallo | pendiente (aún sin sincronizar). */
export const ESTADO_FUENTE = {
  ok: { texto: 'Disponible', tono: 'ok' },
  fallo: { texto: 'Integración fallida', tono: 'bad' },
  pendiente: { texto: 'Sin sincronizar', tono: 'warn' },
}

/** Mensaje claro para el docente a partir de un ApiError. */
export function mensajeError(e, contexto) {
  if (!e) return ''
  if (e.estado === 0) {
    return `${contexto}: no se pudo conectar con el servidor. Si está en el plan gratuito, ` +
      'puede estar despertando (hasta 1 minuto); vuelve a intentarlo.'
  }
  if (e.estado === 401) return 'Tu sesión venció. Vuelve a iniciar sesión.'
  const detalle = typeof e.detalle === 'string' && e.detalle ? e.detalle : `error ${e.estado}`
  return `${contexto}: ${detalle}`
}
