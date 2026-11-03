/**
 * Semana 10 · Captura las pantallas de HU-006 (indicadores I1–I4 con ayuda) y
 * HU-007 (lista y detalle de las alertas R1–R4).
 *
 * Uso:  node scripts/capturar-semana10.mjs
 * Requiere el servidor de desarrollo en URL_BASE (por defecto :5173).
 */
import { chromium } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5173'
const SALIDA = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana10')

await mkdir(SALIDA, { recursive: true })
const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
const foto = async (nombre, opciones = {}) => {
  await page.screenshot({ path: path.join(SALIDA, `${nombre}.png`), ...opciones })
  console.log('ok', nombre)
}

/** Lee lo que el Dashboard muestra en sus cuatro tarjetas de indicadores. */
const leerIndicadores = () => page.locator('#dash-indicadores').locator('..').locator('.stat').evaluateAll(
  tarjetas => Object.fromEntries(tarjetas.map(t => {
    const etiqueta = t.querySelector('small').innerText.replace('?', '').trim()
    return [etiqueta.match(/\((I\d)\)/)[1], t.querySelector('strong').innerText.trim()]
  })))
const mostrado = {}

/** Recorte de una sección con margen extra abajo, para que entre la ayuda desplegada. */
async function recorte(nombre, localizador, extraBajo = 0) {
  const caja = await localizador.boundingBox()
  await foto(nombre, { clip: { x: Math.max(caja.x - 12, 0), y: caja.y - 12, width: caja.width + 24, height: caja.height + extraBajo + 24 } })
}

await page.goto(`${BASE}/#login`)
await page.getByLabel('Correo del docente').fill('docente1@demo.test')
await page.locator('input[type=password]').fill('DemoDocente2026!')
await page.locator('input[type=password]').press('Enter')
await page.waitForSelector('nav[aria-label="Navegación docente"]')

// --- HU-006 · proyecto 1 --------------------------------------------------
await page.getByRole('button', { name: 'Dashboard', exact: true }).click()
await page.waitForSelector('#dash-indicadores')
await foto('01_dashboard_proyecto1', { fullPage: true })
mostrado['1'] = await leerIndicadores()

const seccion = page.locator('#dash-indicadores').locator('..').locator('.grid.cuatro')
await page.getByRole('button', { name: /Cómo se calcula: I1/ }).hover()
await recorte('02_ayuda_I1_raton', seccion, 70)
await page.mouse.move(0, 0)

await page.getByRole('button', { name: /Cómo se calcula: I3/ }).focus() // con teclado
await recorte('03_ayuda_I3_teclado', seccion, 70)
await page.keyboard.press('Escape')
await recorte('04_ayuda_I3_cerrada_con_Esc', seccion, 70)

// --- proyecto 2 (dispara R1, R2, R3 y R4) ---------------------------------
await page.getByRole('button', { name: 'Mis proyectos', exact: true }).first().click()
await page.getByRole('button', { name: 'Ver proyecto' }).nth(1).click()
await page.getByRole('button', { name: 'Ver Dashboard' }).click()
await page.waitForSelector('#dash-indicadores')
await foto('05_dashboard_proyecto2', { fullPage: true })
mostrado['2'] = await leerIndicadores()
await writeFile(path.join(SALIDA, 'HU-006_valores_dashboard.json'), JSON.stringify(mostrado, null, 2), 'utf-8')
console.log('indicadores mostrados:', JSON.stringify(mostrado))
await page.getByRole('button', { name: /Cómo se calcula: I4/ }).hover()
await recorte('06_ayuda_I4_raton', seccion, 70)
await page.mouse.move(0, 0)

// --- HU-007 · lista y detalle ---------------------------------------------
const alertas = page.locator('#dash-alerta').locator('..')
await recorte('07_lista_alertas_todas', alertas)

for (const regla of ['R1', 'R2', 'R3', 'R4']) {
  await page.getByRole('button', { name: new RegExp(`^${regla} \\(`) }).click()
  await recorte(`08_lista_filtro_${regla}`, alertas)
  await page.getByRole('button', { name: /Ver detalle y evidencia/ }).first().click()
  await page.waitForSelector('#alerta-explicacion')
  await foto(`09_detalle_alerta_${regla}`, { fullPage: true })
  await page.getByRole('button', { name: 'Volver al Dashboard' }).click()
  await page.waitForSelector('#dash-alerta')
}

await browser.close()
