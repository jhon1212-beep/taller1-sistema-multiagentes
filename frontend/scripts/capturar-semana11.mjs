/**
 * Semana 11 · Mondragón · TA-044, HU-009, TA-040 y TA-024.
 *
 * Con la API real (FastAPI) y el frontend conectado a ella:
 *   TA-044 · vista de validación funcional con resultado PASS y FAIL.
 *   HU-009 · historial de cortes + reporte imprimible (PDF) + 5 verificaciones.
 *   TA-040 · Dashboard, alertas e historial leen la API; tabla de comparación.
 *   TA-024 · revisión de consistencia visual de las pantallas del Sprint 2.
 *
 * Requiere:
 *   - la API en API_URL (por defecto http://localhost:8000) con SUPERVISION_SOURCES=dataset,
 *     E2E_EJECUTOR=falso y un docente con 2 proyectos (el 2.º con «falla» en su URL), y
 *   - el frontend en URL_BASE arrancado con VITE_API_URL apuntando a esa API:
 *       VITE_API_URL=http://localhost:8000 npm run dev -- --host 127.0.0.1 --port 5173
 *
 * Uso:  node scripts/capturar-semana11.mjs
 * Escribe docs/sprint2/evidencias/semana11/*
 */
import { chromium } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5173'
const API = process.env.API_URL ?? 'http://localhost:8000'
const CORREO = process.env.E2E_CORREO ?? 'docente@upao.test'
const CLAVE = process.env.E2E_CLAVE ?? 'Demo-2026'
const SALIDA = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana11')
await mkdir(SALIDA, { recursive: true })

const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
const foto = async (nombre, opciones = {}) => {
  await page.screenshot({ path: path.join(SALIDA, `${nombre}.png`), ...opciones })
  console.log('ok', nombre)
}
const guardar = (nombre, dato) => writeFile(path.join(SALIDA, nombre), typeof dato === 'string' ? dato : JSON.stringify(dato, null, 2), 'utf-8')

// --- Lo que responde el servidor (para comparar con lo que muestra la pantalla) ---
const sesion = await (await fetch(`${API}/auth/login`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ correo: CORREO, password: CLAVE }),
})).json()
const pedir = async (ruta, metodo = 'GET', cuerpo) => (await fetch(`${API}${ruta}`, {
  method: metodo,
  headers: { Authorization: `Bearer ${sesion.token}`, ...(cuerpo ? { 'Content-Type': 'application/json' } : {}) },
  body: cuerpo ? JSON.stringify(cuerpo) : undefined,
})).json()
const proyectos = await pedir('/proyectos')
const P1 = proyectos.find(p => p.nombre === 'Proyecto demo Grupo 8')
const P2 = proyectos.find(p => p.nombre === 'Proyecto piloto con falla')
console.log('proyectos', P1.id, P2.id)

// --- Entrar -------------------------------------------------------------------
await page.goto(`${BASE}/#login`)
await page.getByLabel('Correo del docente').fill(CORREO)
await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
await page.getByRole('button', { name: 'Ingresar' }).click()
await page.getByRole('heading', { name: 'Mis proyectos' }).waitFor()
await page.getByText(P1.nombre).first().waitFor()

async function abrirProyecto(nombre) {
  await page.getByRole('button', { name: 'Mis proyectos', exact: true }).first().click()
  await page.getByRole('heading', { name: 'Mis proyectos' }).waitFor()
  const fila = page.locator('tr, .card', { hasText: nombre }).first()
  await fila.getByRole('button', { name: 'Ver proyecto' }).click()
}

// ==== TA-040 · Dashboard con la API real =========================================
await abrirProyecto(P1.nombre)
await page.getByRole('button', { name: 'Ver Dashboard' }).click()
await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor()
await foto('TA-040_01_dashboard_antes_de_ejecutar', { fullPage: true })

for (const dia of ['2026-10-06', '2026-10-12']) {
  await page.getByLabel('Fecha de corte').fill(dia)
  await page.getByRole('button', { name: 'Ejecutar supervisión' }).click()
  await page.locator('.traza').filter({ hasText: `corte ${dia}` }).waitFor()
}
await page.waitForTimeout(800)
await foto('TA-040_02_dashboard_corte_12_oct', { fullPage: true })

const leer = etiqueta => page.locator('.stat', { hasText: etiqueta }).locator('strong').innerText()
const pantalla = {
  I1: await leer('(I1)'), I2: await leer('(I2)'), I3: await leer('(I3)'), I4: await leer('(I4)'),
}
const apiInd = await pedir(`/proyectos/${P1.id}/indicadores?fecha_corte=2026-10-12`)
const apiAle = await pedir(`/proyectos/${P1.id}/alertas?fecha_corte=2026-10-12`)
await guardar('TA-040_api_indicadores.json', apiInd)
await guardar('TA-040_api_alertas.json', apiAle)
await guardar('TA-040_pantalla_indicadores.json', pantalla)

// Alertas: lista y detalle de la primera de cada regla presente
const reglas = [...new Set(apiAle.alertas.map(a => a.regla))].sort()
const alertasPantalla = {}
const alertasSeccion = page.locator('#dash-alerta').locator('..')
await alertasSeccion.scrollIntoViewIfNeeded()
await foto('TA-040_03_lista_de_alertas', { clip: await caja(alertasSeccion) })
async function caja(loc) {
  const c = await loc.boundingBox()
  return { x: Math.max(c.x - 12, 0), y: Math.max(c.y - 12, 0), width: c.width + 24, height: c.height + 24 }
}
for (const regla of reglas) {
  await page.getByRole('button', { name: new RegExp(`^${regla} \\(`) }).click()
  await page.getByRole('button', { name: /Ver detalle y evidencia/ }).first().click()
  await page.waitForSelector('#alerta-explicacion')
  alertasPantalla[regla] = {
    explicacion: (await page.locator('#alerta-explicacion').locator('..').innerText()).slice(0, 400),
  }
  await foto(`TA-040_04_detalle_alerta_${regla}`, { fullPage: true })
  await page.getByRole('button', { name: 'Volver al Dashboard' }).click()
  await page.waitForSelector('#dash-alerta')
}
await guardar('TA-040_pantalla_alertas.json', alertasPantalla)

// ==== HU-009 · Historial y reporte imprimible ====================================
await page.getByRole('button', { name: 'Ver historial de cortes' }).click()
await page.getByRole('heading', { name: 'Historial de supervisión' }).waitFor()
await page.getByRole('heading', { name: 'Comparación entre cortes' }).waitFor()
await foto('HU-009_01_historial_cortes', { fullPage: true })
const apiHist = await pedir(`/proyectos/${P1.id}/historial`)
await guardar('HU-009_api_historial.json', apiHist)

const tablaHist = await page.locator('table').first().evaluate(t =>
  [...t.querySelectorAll('tbody tr')].map(tr => [...tr.cells].map(c => c.innerText.trim())))
await guardar('HU-009_pantalla_historial.json', tablaHist)

// Reporte imprimible: vista de impresión + PDF
await page.emulateMedia({ media: 'print' })
await foto('HU-009_02_reporte_vista_impresion', { fullPage: true })
const ocultosEnImpresion = await page.evaluate(() =>
  [...document.querySelectorAll('.no-imprimir')].map(e => getComputedStyle(e).display))
const visiblesSoloImpresion = await page.evaluate(() =>
  [...document.querySelectorAll('.solo-imprimir')].map(e => getComputedStyle(e).display))
const textoEmision = await page.locator('.solo-imprimir').first().innerText().catch(() => '')
await page.pdf({ path: path.join(SALIDA, 'HU-009_reporte_imprimible.pdf'), format: 'A4', printBackground: true })
console.log('ok HU-009_reporte_imprimible.pdf')
await page.emulateMedia({ media: 'screen' })

// ==== TA-044 · Validación funcional PASS y FAIL ==================================
async function validar(nombre, etiqueta) {
  await abrirProyecto(nombre)
  await page.getByRole('button', { name: 'Ver Dashboard' }).click()
  await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Ver validación' }).click()
  await page.getByRole('heading', { name: 'Verificación de la aplicación' }).waitFor()
  await foto(`TA-044_${etiqueta}_0_antes_de_ejecutar`, { fullPage: true })
  await page.getByRole('button', { name: 'Ejecutar validación' }).click()
  await page.getByRole('heading', { name: 'Último resultado' }).waitFor({ timeout: 60_000 })
  await page.waitForTimeout(500)
  await foto(`TA-044_${etiqueta}_1_resultado`, { fullPage: true })
  return page.locator('.validacion-resultado .pill').first().innerText()
}
const resultadoPass = await validar(P1.nombre, 'PASS')
const resultadoFail = await validar(P2.nombre, 'FAIL')
console.log('validaciones', resultadoPass, resultadoFail)
const apiVal1 = await pedir(`/proyectos/${P1.id}/validaciones`)
const apiVal2 = await pedir(`/proyectos/${P2.id}/validaciones`)
await guardar('TA-044_api_validaciones.json', { proyecto1: apiVal1, proyecto2: apiVal2 })

// Se ejecuta otra vez la validación del proyecto 1 y se vuelve a capturar el historial,
// que muestra la validación CP-17 del día en su columna.
await abrirProyecto(P1.nombre)
await page.getByRole('button', { name: 'Ver Dashboard' }).click()
const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Lima' })
await page.getByLabel('Fecha de corte').fill(hoy)
await page.getByRole('button', { name: 'Ejecutar supervisión' }).click()
await page.locator('.traza').filter({ hasText: `corte ${hoy}` }).waitFor()
await page.getByRole('button', { name: 'Ver historial de cortes' }).click()
await page.getByRole('heading', { name: 'Comparación entre cortes' }).waitFor()
await guardar('HU-009_api_historial_final.json', await pedir(`/proyectos/${P1.id}/historial`))
await guardar('HU-009_pantalla_historial_final.json', await page.locator('table').first().evaluate(t =>
  [...t.querySelectorAll('tbody tr')].map(tr => [...tr.cells].map(c => c.innerText.trim()))))
await page.emulateMedia({ media: 'print' })
await foto('HU-009_04_reporte_impresion_final', { fullPage: true })
await page.pdf({ path: path.join(SALIDA, 'HU-009_reporte_imprimible.pdf'), format: 'A4', printBackground: true })
await page.emulateMedia({ media: 'screen' })
await foto('HU-009_03_historial_con_validacion', { fullPage: true })

// ==== Resultado de las comprobaciones ============================================
await guardar('resumen_pantalla.json', {
  proyecto1: P1.id, proyecto2: P2.id, pantalla, resultadoPass, resultadoFail,
  ocultosEnImpresion, visiblesSoloImpresion, textoEmision, reglas,
})

await browser.close()
