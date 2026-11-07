/**
 * TA-039 · Verifica que el frontend conectado a la API muestra lo mismo que
 * el servidor y que el dato de origen (5 de 5 por fuente), y captura las pantallas.
 *
 * Requiere:
 *   - la API real en API_URL (python backend/scripts/demo_api_real.py), y
 *   - el frontend en URL_BASE arrancado con VITE_API_URL apuntando a esa API:
 *       VITE_API_URL=http://127.0.0.1:8000 npm run dev -- --port 5174
 *
 * Uso:  node scripts/verificar-api-semana10.mjs
 * Escribe docs/sprint2/evidencias/semana10/TA-039_* (capturas, JSON y tabla).
 */
import { chromium } from '@playwright/test'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5174'
const API = process.env.API_URL ?? 'http://127.0.0.1:8000'
const RAIZ = path.resolve(AQUI, '../..')
const SALIDA = path.join(RAIZ, 'docs/sprint2/evidencias/semana10')
const CORREO = 'docente1@demo.test'
const CLAVE = 'DemoDocente2026!'
const PROYECTO = 1
const N = 5

await mkdir(SALIDA, { recursive: true })

// --- Dato de origen: el dataset controlado de TA-017 --------------------------
const dataset = JSON.parse(await readFile(path.join(RAIZ, 'backend/app/modulos/evidencias/dataset/proyecto_demo.json'), 'utf-8'))
const origen = fuente => dataset.evidencias.filter(e => e.proyecto_id === PROYECTO && e.fuente === fuente)
const recientesPrimero = lista => [...lista].sort((a, b) => b.fecha.localeCompare(a.fecha))
// Siempre en UTC: la API devuelve la hora con el desfase de la zona del servidor.
const f16 = iso => new Date(iso).toISOString().slice(0, 16).replace('T', ' ')

// --- Lo que responde el servidor ---------------------------------------------
const sesion = await (await fetch(`${API}/auth/login`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ correo: CORREO, password: CLAVE }),
})).json()
const pedir = async ruta => (await fetch(`${API}${ruta}`, { headers: { Authorization: `Bearer ${sesion.token}` } })).json()
const apiCommits = await pedir(`/proyectos/${PROYECTO}/commits`)
const apiTareas = await pedir(`/proyectos/${PROYECTO}/tareas`)
const apiDocs = await pedir(`/proyectos/${PROYECTO}/documentos`)
const apiProyectos = await pedir('/proyectos')

const esperado = {
  github: {
    columnas: ['Autor', 'Fecha', 'Mensaje', 'SHA corto'],
    api: apiCommits.items.map(c => [c.autor, f16(c.fecha), c.mensaje, c.sha.slice(0, 7)]),
    origen: recientesPrimero(origen('github')).map(e => [e.autor, f16(e.fecha), e.descripcion, e.id_externo.slice(0, 7)]),
  },
  notion: {
    columnas: ['Tarea', 'Responsable', 'Estado', 'Fecha límite'],
    api: apiTareas.tareas.map(t => [t.tarea, t.responsable ?? 'Sin responsable', t.estado, t.fecha_limite ?? '—']),
    origen: origen('notion').map(e => [e.descripcion, e.autor ?? 'Sin responsable', e.estado, e.fecha_limite ?? '—']),
  },
  drive: {
    columnas: ['Nombre', 'Último editor', 'Última modificación', 'Tipo'],
    api: apiDocs.items.map(d => [d.nombre, d.ultimo_editor, f16(d.fecha), d.tipo ?? '—']),
    origen: recientesPrimero(origen('drive')).map(e => [e.descripcion, e.autor, f16(e.fecha), e.tipo_archivo ?? '—']),
  },
}

// --- Navegador ----------------------------------------------------------------
const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
const foto = async (nombre, opciones = { fullPage: true }) => {
  await page.screenshot({ path: path.join(SALIDA, `TA-039_${nombre}.png`), ...opciones })
  console.log('ok', nombre)
}
const filasUI = () => page.locator('table tbody tr').evaluateAll(
  filas => filas.map(f => [...f.querySelectorAll('td')].map(td => td.innerText.trim())))

// 1. Inicio de sesión real: error y acierto
await page.goto(`${BASE}/#login`)
await foto('01_login_api')
await page.getByLabel('Correo del docente').fill(CORREO)
await page.getByLabel('Contraseña', { exact: true }).fill('clave-que-no-es')
await page.getByRole('button', { name: 'Ingresar' }).click()
await page.getByRole('alert').waitFor()
const mensajeError = (await page.getByRole('alert').innerText()).trim()
await foto('02_login_rechazado_por_el_servidor')
await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
await page.getByRole('button', { name: 'Ingresar' }).click()
await page.getByRole('heading', { name: 'Mis proyectos' }).waitFor()
await page.getByText('Biblioteca digital').first().waitFor()

// 2. Proyectos que llegan de la API
const nombresUI = await page.locator('.card h3').allInnerTexts().catch(() => [])
await foto('03_mis_proyectos_desde_la_api')

// 3. Detalle del proyecto y las tres fuentes
await page.getByRole('button', { name: 'Ver proyecto' }).first().click()
await page.getByText('Commits guardados').waitFor()
await page.waitForFunction(() => !document.body.innerText.includes('…'))
await foto('04_detalle_resumen_desde_la_api')

const resultado = {}
const pestanas = [['github', 'GitHub', '05_commits_github'], ['notion', 'Notion', '06_tareas_notion'], ['drive', 'Google Drive', '07_documentos_drive']]
for (const [fuente, pestana, archivo] of pestanas) {
  await page.getByRole('tab', { name: pestana }).click()
  await page.locator('table tbody tr').first().waitFor()
  const ui = await filasUI()
  await foto(archivo)
  const e = esperado[fuente]
  const filas = Array.from({ length: N }, (_, i) => {
    const u = (ui[i] ?? []).join(' | '), a = (e.api[i] ?? []).join(' | '), o = (e.origen[i] ?? []).join(' | ')
    return { n: i + 1, ui: u, api: a, origen: o, coincide: u === a && a === o && u !== '' }
  })
  resultado[fuente] = {
    columnas: e.columnas,
    filas,
    aciertos: filas.filter(f => f.coincide).length,
    total_ui: ui.length, total_api: e.api.length, total_origen: e.origen.length,
  }
}

// 4. Alta y desactivación de un proyecto contra el servidor
await page.getByRole('button', { name: 'Mis proyectos', exact: true }).first().click()
await page.getByRole('button', { name: '+ Registrar proyecto' }).click()
const datos = {
  'Nombre del proyecto': 'Proyecto de prueba TA-039', 'Curso': 'Taller Integrador 1',
  'Fecha de inicio': '2026-10-01', 'Fecha de fin': '2026-12-15',
  'Repositorio de GitHub': 'https://github.com/demo/ta-039', 'Base de tareas de Notion': 'https://notion.so/ta-039',
  'Carpeta de Google Drive': 'https://drive.google.com/drive/folders/ta-039',
  'URL pública de la aplicación': 'https://example.org', 'Elemento a verificar (selector CSS)': 'h1',
}
for (const [etiqueta, valor] of Object.entries(datos)) await page.getByLabel(etiqueta, { exact: false }).first().fill(valor)
await page.getByLabel(/Integrantes del equipo/).fill('Ana Torres, Luis Vega')
await foto('08_formulario_nuevo_proyecto')
await page.getByRole('button', { name: 'Guardar proyecto' }).click()
await page.getByText('Proyecto guardado en el servidor.').waitFor()
await foto('09_proyecto_guardado_en_el_servidor')
const tras = await pedir('/proyectos')
const creado = tras.find(p => p.nombre === 'Proyecto de prueba TA-039')

const tarjeta = page.locator('.card', { hasText: 'Proyecto de prueba TA-039' })
await tarjeta.getByRole('button', { name: 'Desactivar' }).click()
await page.getByText('Proyecto desactivado en el servidor.').waitFor()
const despues = await pedir('/proyectos?incluir_inactivos=true')
const desactivado = despues.find(p => p.nombre === 'Proyecto de prueba TA-039')

// 5. Cerrar sesión
await page.getByRole('button', { name: 'Cerrar sesión' }).click()
await page.getByRole('heading', { name: 'Iniciar sesión' }).waitFor()
await foto('10_sesion_cerrada')
await browser.close()

// --- Resultado ----------------------------------------------------------------
const resumen = {
  fecha: new Date().toISOString(),
  proyecto_id: PROYECTO,
  login_rechazado: mensajeError,
  proyectos_api: apiProyectos.map(p => p.nombre),
  proyectos_ui_coinciden: apiProyectos.every(p => nombresUI.includes(p.nombre)),
  fuentes: resultado,
  alta_proyecto: { creado_en_servidor: Boolean(creado), id: creado?.id ?? null },
  desactivar_proyecto: { activo_en_servidor: desactivado?.activo ?? null },
}
await writeFile(path.join(SALIDA, 'TA-039_comparacion.json'), JSON.stringify(resumen, null, 2), 'utf-8')

const nombres = { github: 'GitHub (commits)', notion: 'Notion (tareas)', drive: 'Google Drive (documentos)' }
let md = '# TA-039 · Comparación pantalla ↔ API ↔ dato de origen\n\n'
md += `Proyecto ${PROYECTO}. «Origen» = dataset controlado de TA-017. Las filas son las ${N} primeras de cada lista.\n\n`
for (const [fuente, r] of Object.entries(resultado)) {
  md += `## ${nombres[fuente]} · ${r.aciertos} de ${N}\n\nTotales: pantalla ${r.total_ui} · API ${r.total_api} · origen ${r.total_origen}\n\n`
  md += `| # | Pantalla | API | Origen | ¿Coincide? |\n|---|---|---|---|---|\n`
  for (const f of r.filas) md += `| ${f.n} | ${f.ui} | ${f.api} | ${f.origen} | ${f.coincide ? 'Sí' : 'NO'} |\n`
  md += '\n'
}
await writeFile(path.join(SALIDA, 'TA-039_comparacion.md'), md, 'utf-8')

for (const [fuente, r] of Object.entries(resultado)) console.log(`${nombres[fuente]}: ${r.aciertos} de ${N} (pantalla ${r.total_ui}, API ${r.total_api}, origen ${r.total_origen})`)
console.log('login rechazado:', mensajeError)
console.log('alta:', resumen.alta_proyecto, 'desactivar:', resumen.desactivar_proyecto)
