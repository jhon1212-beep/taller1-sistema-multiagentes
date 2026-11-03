/**
 * HU-008 · Consultar la validación funcional (CP-17) · prueba Playwright contra la API real.
 *
 * Qué demuestra, de principio a fin y sin simulaciones del lado del cliente:
 *   1. Se registran dos validaciones de verdad (POST /validaciones): una PASS y una FAIL.
 *      El servidor las ejecuta con Playwright (E2E_EJECUTOR=local → validar-url.mjs).
 *   2. Las dos rutas nuevas las devuelven:
 *        GET /proyectos/{id}/validaciones          historial y recuento
 *        GET /proyectos/{id}/validaciones/ultima   la más reciente (404 si no hay)
 *   3. La documentación Swagger muestra ambas rutas y el navegador renderiza las respuestas.
 *
 * Requisitos: API en API_URL con base migrada y un docente (CORREO / CLAVE). La página
 * que se valida es GET /health de la propia API: así no hace falta ningún otro servidor.
 *
 *   API_URL=http://127.0.0.1:8000 CORREO=docente1@demo.test CLAVE=... npx playwright test
 *
 * Capturas: SALIDA (por defecto ../docs/sprint2/evidencias/semana10_castro/). El reporte
 * HTML queda en e2e/playwright-report/.
 */
import { expect, test } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const API = process.env.API_URL ?? 'http://127.0.0.1:8000'
const CORREO = process.env.CORREO ?? 'docente1@demo.test'
const CLAVE = process.env.CLAVE ?? 'DemoDocente2026!'
const SALIDA = process.env.SALIDA ?? path.resolve(AQUI, '../docs/sprint2/evidencias/semana10_castro')

test.describe.configure({ mode: 'serial' })

let token
let cabeceras
const proyectos = {} // { pass: id, fail: id }
const sello = Date.now()

async function crearProyecto(request, nombre, selector) {
  const r = await request.post(`${API}/proyectos`, {
    data: {
      nombre, curso: 'Taller Integrador 1', fecha_inicio: '2026-09-21', fecha_fin: '2026-11-30',
      url_publica: `${API}/health`, elemento_verificar: selector,
      integrantes: [{ nombre: 'Ana Torres', correo: null }],
      fuentes: { github: 'o/r', notion: 'n', drive: 'd' },
    },
  })
  expect(r.status()).toBe(201)
  return (await r.json()).id
}

test.beforeAll(async ({ request }) => {
  await mkdir(SALIDA, { recursive: true })
  const login = await request.post(`${API}/auth/login`, { data: { correo: CORREO, password: CLAVE } })
  expect(login.status(), 'inicio de sesión del docente').toBe(200)
  token = (await login.json()).token
  cabeceras = { Authorization: `Bearer ${token}` }
})

test('HU-008 · se registran una validación PASS y otra FAIL con el Playwright del servidor', async ({ request }) => {
  proyectos.pass = await crearProyecto(request, `Validación PASS ${sello}`, 'pre')
  proyectos.fail = await crearProyecto(request, `Validación FAIL ${sello}`, '#elemento-que-no-existe')

  const ok = await request.post(`${API}/validaciones`, { headers: cabeceras, data: { proyecto_id: proyectos.pass } })
  expect(ok.status()).toBe(201)
  const pass = await ok.json()
  expect(pass).toMatchObject({ proyecto_id: proyectos.pass, resultado: 'PASS', captura_url: null })

  const mal = await request.post(`${API}/validaciones`, { headers: cabeceras, data: { proyecto_id: proyectos.fail } })
  expect(mal.status()).toBe(201)
  const fail = await mal.json()
  expect(fail).toMatchObject({ proyecto_id: proyectos.fail, resultado: 'FAIL' })
  expect(fail.captura_url, 'un FAIL guarda la captura de la pantalla').toBeTruthy()
})

test('HU-008 · la ruta de historial devuelve la validación y su recuento', async ({ request }) => {
  const pass = await (await request.get(`${API}/proyectos/${proyectos.pass}/validaciones`, { headers: cabeceras })).json()
  expect(pass.resumen).toEqual({ PASS: 1, FAIL: 0 })
  expect(pass.items).toHaveLength(1)
  expect(pass.items[0]).toMatchObject({ resultado: 'PASS', captura_url: null })
  expect(Number(pass.items[0].duracion_ms)).toBeGreaterThan(0)

  const fail = await (await request.get(`${API}/proyectos/${proyectos.fail}/validaciones?resultado=FAIL&limite=5`, { headers: cabeceras })).json()
  expect(fail.resumen).toEqual({ PASS: 0, FAIL: 1 })
  expect(fail.items[0].captura_url).toContain('captura.png')
})

test('HU-008 · la ruta «ultima» devuelve la más reciente y 404 si el proyecto no se validó', async ({ request }) => {
  const ultima = await request.get(`${API}/proyectos/${proyectos.fail}/validaciones/ultima`, { headers: cabeceras })
  expect(ultima.status()).toBe(200)
  expect((await ultima.json()).resultado).toBe('FAIL')

  const sinValidar = await crearProyecto(request, `Sin validar ${sello}`, 'pre')
  const vacio = await request.get(`${API}/proyectos/${sinValidar}/validaciones/ultima`, { headers: cabeceras })
  expect(vacio.status()).toBe(404)
  const historial = await (await request.get(`${API}/proyectos/${sinValidar}/validaciones`, { headers: cabeceras })).json()
  expect(historial).toMatchObject({ resumen: { PASS: 0, FAIL: 0 }, items: [] })
})

test('HU-008 · las rutas exigen sesión y respetan los parámetros', async ({ request }) => {
  const sinToken = await request.get(`${API}/proyectos/${proyectos.pass}/validaciones`)
  expect(sinToken.status()).toBe(401)
  for (const consulta of ['resultado=MAL', 'limite=0', 'limite=101']) {
    const r = await request.get(`${API}/proyectos/${proyectos.pass}/validaciones?${consulta}`, { headers: cabeceras })
    expect(r.status(), consulta).toBe(422)
  }
})

test('HU-008 · captura de la pantalla: Swagger con las rutas y las respuestas en el navegador', async ({ browser }, testInfo) => {
  const contexto = await browser.newContext({ extraHTTPHeaders: cabeceras, viewport: { width: 1280, height: 900 } })
  const pagina = await contexto.newPage()
  const guardar = async (nombre, opciones = {}) => {
    const ruta = path.join(SALIDA, `${nombre}.png`)
    await pagina.screenshot({ path: ruta, ...opciones })
    await testInfo.attach(nombre, { path: ruta, contentType: 'image/png' })
  }

  // La documentación de la API: las dos rutas nuevas bajo la etiqueta «validacion»
  await pagina.goto(`${API}/docs`)
  const seccion = pagina.locator('.opblock-tag-section', { hasText: 'validacion' })
  await expect(seccion.getByText('/proyectos/{proyecto_id}/validaciones/ultima')).toBeVisible({ timeout: 30_000 })
  await seccion.scrollIntoViewIfNeeded()
  await guardar('HU-008_01_swagger_rutas_de_validacion', {
    clip: await seccion.boundingBox() ? { ...(await seccion.boundingBox()), x: 0, width: 1280 } : undefined,
  })

  // Lo que devuelve el servidor, tal como lo ve el navegador (con la sesión del docente)
  for (const [nombre, ruta] of [
    ['02_historial_proyecto_fail', `/proyectos/${proyectos.fail}/validaciones`],
    ['03_ultima_proyecto_fail', `/proyectos/${proyectos.fail}/validaciones/ultima`],
    ['04_historial_proyecto_pass', `/proyectos/${proyectos.pass}/validaciones`],
  ]) {
    await pagina.goto(`${API}${ruta}`)
    await expect(pagina.locator('body')).toContainText('"resultado"')
    const sangria = pagina.locator('input[type=checkbox]').first() // «Pretty print» del visor JSON
    if (await sangria.count()) await sangria.check()
    await guardar(`HU-008_${nombre}`, { clip: { x: 0, y: 0, width: 1280, height: 460 } })
  }
  await contexto.close()
})
