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
    const detalle = await respuesta.text().catch(() => '')
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
export const API_ACTIVA = true
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
