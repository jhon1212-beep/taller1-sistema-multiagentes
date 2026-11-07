// AR-03 · Capa de acceso a la API del backend (FastAPI).
// Las vistas deben consumir estas funciones y no usar fetch directamente.

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(mensaje, estado, detalle) {
    super(mensaje)
    this.name = 'ApiError'
    this.estado = estado
    this.detalle = detalle
  }
}

// TA-039 · Token de la sesión. Vive solo en memoria: se pierde al recargar la
// página, igual que el resto del estado de la sesión.
let tokenSesion = null
export const establecerToken = token => { tokenSesion = token }

// TA-040 · Si el servidor responde 401 con una sesión abierta (token vencido o
// servidor reiniciado con otro JWT_SECRET), App cierra la sesión y avisa.
let alVencerSesion = () => {}
export const alExpirarSesion = funcion => { alVencerSesion = funcion }

async function solicitar(ruta, { metodo = 'GET', cuerpo, parametros, senal } = {}) {
  const url = new URL(`${BASE_URL}${ruta}`)
  Object.entries(parametros ?? {}).forEach(([clave, valor]) => {
    if (valor !== undefined && valor !== null) url.searchParams.set(clave, valor)
  })

  let respuesta
  try {
    respuesta = await fetch(url, {
      method: metodo,
      headers: {
        Accept: 'application/json',
        ...(cuerpo ? { 'Content-Type': 'application/json' } : {}),
        ...(tokenSesion ? { Authorization: `Bearer ${tokenSesion}` } : {}),
      },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
      signal: senal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('No se pudo conectar con el servidor', 0, error.message)
  }

  if (!respuesta.ok) {
    const texto = await respuesta.text().catch(() => '')
    // FastAPI responde { "detail": "..." }; se guarda ese mensaje para mostrarlo tal cual.
    let detalle = texto
    try { detalle = JSON.parse(texto).detail ?? texto } catch { /* no era JSON */ }
    if (respuesta.status === 401 && tokenSesion && ruta !== '/auth/login') alVencerSesion()
    throw new ApiError(`Error ${respuesta.status} en ${ruta}`, respuesta.status, detalle)
  }
  return respuesta.status === 204 ? null : respuesta.json()
}

export const api = {
  get: (ruta, opciones) => solicitar(ruta, { ...opciones, metodo: 'GET' }),
  post: (ruta, cuerpo, opciones) => solicitar(ruta, { ...opciones, metodo: 'POST', cuerpo }),
  put: (ruta, cuerpo, opciones) => solicitar(ruta, { ...opciones, metodo: 'PUT', cuerpo }),
  patch: (ruta, opciones) => solicitar(ruta, { ...opciones, metodo: 'PATCH' }),
}

/** Estado del backend: { status: 'ok' } */
export const obtenerEstado = (opciones) => api.get('/health', opciones)

/** true si el build define VITE_API_URL; si no, las vistas usan datos de demostración. */
export const API_ACTIVA = import.meta.env.VITE_API_URL !== undefined
/**
 * HU-001 · Inicio de sesión del docente.
 * { token, tipo, expira_en, docente: { id, nombre, correo } }
 */
export const iniciarSesion = (correo, password) => api.post('/auth/login', { correo, password })

/** HU-001 · Cierra la sesión en el servidor (204). */
export const cerrarSesionApi = () => api.post('/auth/logout')

/** HU-002 · Proyectos del docente (con los desactivados, para el filtro de la lista). */
export const obtenerProyectos = (opciones) =>
  api.get('/proyectos', { ...opciones, parametros: { incluir_inactivos: true } })
export const crearProyecto = (cuerpo) => api.post('/proyectos', cuerpo)
export const editarProyecto = (id, cuerpo) => api.put(`/proyectos/${id}`, cuerpo)
export const desactivarProyecto = (id) => api.patch(`/proyectos/${id}/desactivar`)

/**
 * HU-004 · Tareas del proyecto desde Notion.
 * { estado: 'ok' | 'fallo', error, total, resumen, tareas: [...] }
 */
export const obtenerTareas = (proyectoId, opciones) =>
  api.get(`/proyectos/${proyectoId}/tareas`, opciones)

/**
 * HU-003 / HU-005 · Commits y documentos guardados del proyecto.
 * { estado_fuente: 'ok' | 'fallo', total, items: [...] }
 */
export const obtenerCommits = (proyectoId, opciones) =>
  api.get(`/proyectos/${proyectoId}/commits`, opciones)
export const obtenerDocumentos = (proyectoId, opciones) =>
  api.get(`/proyectos/${proyectoId}/documentos`, opciones)

// -- Sprint 2 · Supervisión (TA-022, módulo supervision) -------------------------

/**
 * TA-022 · Ejecuta los agentes (Supervisor → GitHub + Notion + Drive → motor → explicación)
 * y guarda el corte. fechaCorte en ISO 8601 con zona; sin ella, fin del día en Lima.
 * { proyecto_id, fecha_corte, fuentes: { github: { estado, error, evidencias } … },
 *   total_evidencias, indicadores, alertas, guardado, duracion_grafo_ms, duracion_servicio_ms }
 */
export const ejecutarConsolidacion = (proyectoId, fechaCorte, opciones) =>
  api.post(`/proyectos/${proyectoId}/consolidacion`,
    fechaCorte ? { fecha_corte: fechaCorte } : {}, opciones)

/**
 * HU-006 · I1–I4 de un corte (AAAA-MM-DD; sin fecha, el más reciente). 404 si no hay corte.
 * { proyecto_id, fecha_corte, indicadores: { I1, I2, I3, I4 }, estado_fuentes }
 */
export const obtenerIndicadores = (proyectoId, fechaCorte, opciones) =>
  api.get(`/proyectos/${proyectoId}/indicadores`,
    { ...opciones, parametros: { fecha_corte: fechaCorte } })

/**
 * HU-007 · Alertas R1–R4 explicadas de un corte, cada una con su evidencia de origen.
 * { proyecto_id, fecha_corte, total, alertas: [{ regla, fuente, evidencia_ids,
 *   explicacion, origen_explicacion, evidencia }] }
 */
export const obtenerAlertas = (proyectoId, fechaCorte, opciones) =>
  api.get(`/proyectos/${proyectoId}/alertas`,
    { ...opciones, parametros: { fecha_corte: fechaCorte } })

/**
 * HU-009 · Todos los cortes del proyecto, del más antiguo al más reciente.
 * { proyecto_id, total_cortes, cortes: [{ fecha_corte, indicadores, total_alertas,
 *   alertas_por_regla, validacion }] }
 */
export const obtenerHistorial = (proyectoId, opciones) =>
  api.get(`/proyectos/${proyectoId}/historial`, opciones)

// -- Sprint 2 · Validación funcional (TA-021, HU-008) ----------------------------

/** TA-021 · Dispara CP-17 (GitHub Actions) y espera su resultado. ValidacionOut (201). */
export const ejecutarValidacion = (proyectoId, opciones) =>
  api.post('/validaciones', { proyecto_id: proyectoId }, opciones)

/** HU-008 · Historial de CP-17: { proyecto_id, resumen: { PASS, FAIL }, items: [...] } */
export const obtenerValidaciones = (proyectoId, opciones) =>
  api.get(`/proyectos/${proyectoId}/validaciones`, { ...opciones, parametros: { limite: 10 } })
