/**
 * TA-005 · Datos de demostración
 *
 * Conjunto simulado que alimenta el prototipo mientras los agentes reales
 * (GitHub, Notion, Drive) no están conectados. Al integrar el backend, este
 * módulo se reemplaza por las llamadas a la API sin tocar las vistas.
 */

export const CUENTAS = Array.from({ length: 5 }, (_, i) => `docente${i + 1}@demo.test`)
export const CLAVE_DEMO = 'DemoDocente2026!'

export const INTEGRANTES = ['Ana Torres', 'Luis Vega', 'Marta Ruiz', 'Diego Paz']

const MENSAJES = [
  'Agregar validación del formulario',
  'Mostrar tareas por proyecto',
  'Corregir filtro de fechas',
  'Documentar ejecución de pruebas',
  'Añadir estados de integración',
]

export const COMMITS = Array.from({ length: 20 }, (_, i) => ({
  autor: INTEGRANTES[i % 4],
  fecha: `2026-10-${String(6 - Math.floor(i / 4)).padStart(2, '0')} 10:${String((i * 3) % 60).padStart(2, '0')}`,
  mensaje: MENSAJES[i % 5],
  sha: (0xa1b2c3d + i * 1237).toString(16).slice(0, 7),
}))

const TITULOS = [
  'Inicio de sesión docente',
  'Registro de proyecto',
  'Listado de commits',
  'Consulta de tareas',
  'Pruebas de integración',
]

export const TAREAS = Array.from({ length: 20 }, (_, i) => ({
  titulo: `${TITULOS[i % 5]} · ${i + 1}`,
  responsable: INTEGRANTES[i % 4],
  estado: i < 8 ? 'Terminado' : i < 14 ? 'En progreso' : 'Pendiente',
  vence: `2026-10-${String(7 + (i % 5)).padStart(2, '0')}`,
}))

export const DOCUMENTOS = Array.from({ length: 10 }, (_, i) => ({
  nombre: `${['Plan del proyecto', 'Arquitectura', 'Plan de pruebas', 'Informe de avance', 'Diseño de interfaz'][i % 5]} · ${i + 1}`,
  editor: INTEGRANTES[i % 4],
  modificado: `2026-10-0${(i % 5) + 1} 14:00`,
  tipo: i % 2 ? 'Documento' : 'PDF',
}))

export const PROYECTOS_INICIALES = [
  {
    id: 1,
    nombre: 'Seguimiento académico',
    curso: 'Taller Integrador 1',
    inicio: '2026-09-21',
    fin: '2026-11-30',
    integrantes: INTEGRANTES.join(', '),
    github: 'https://github.com/demo/seguimiento',
    notion: 'https://notion.so/demo-backlog',
    drive: 'https://drive.google.com/drive/folders/demo',
    url: 'https://example.org',
    selector: 'h1',
    activo: true,
  },
  {
    id: 2,
    nombre: 'Biblioteca digital',
    curso: 'Ingeniería de Software',
    inicio: '2026-09-21',
    fin: '2026-11-30',
    integrantes: 'Elena Ríos, Carlos León',
    github: 'https://github.com/demo/biblioteca',
    notion: 'https://notion.so/demo-biblioteca',
    drive: 'https://drive.google.com/drive/folders/demo-biblioteca',
    url: 'https://example.org',
    selector: '#catalogo',
    activo: true,
  },
]

/** Tono del indicador según el estado de una tarea. */
export const tonoEstado = estado =>
  estado === 'Terminado' ? 'ok' : estado === 'En progreso' ? 'warn' : 'neutro'
