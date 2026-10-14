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
}

/** Estado del backend: { status: 'ok' } */
export const obtenerEstado = (opciones) => api.get('/health', opciones)
