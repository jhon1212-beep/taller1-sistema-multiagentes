/** Semana 9 · TA-020: estados del Dashboard (normal, simulado, fuente caída, móvil). */
import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5173'
const SALIDA = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana9/ta020')
await mkdir(SALIDA, { recursive: true })

const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
const foto = (n, o = {}) => page.screenshot({ path: path.join(SALIDA, n), ...o })

await page.goto(`${BASE}/#login`)
await page.getByLabel('Correo del docente').fill('docente1@demo.test')
await page.locator('input[type=password]').fill('DemoDocente2026!')
await page.locator('input[type=password]').press('Enter')
await page.waitForSelector('nav[aria-label="Navegación docente"]')

await page.evaluate(() => { window.location.hash = 'dashboard' })
await page.waitForTimeout(300)
await foto('01_estructura_completa.png', { fullPage: true })
await foto('02_tarjetas_indicadores.png', { clip: { x: 238, y: 270, width: 1042, height: 220 } })
await foto('03_estado_fuentes_ok.png', { clip: { x: 238, y: 510, width: 1042, height: 210 } })

await page.getByRole('button', { name: 'Simular supervisión' }).click()
await page.waitForTimeout(300)
await foto('04_simulacion_traza.png', { fullPage: true })

// Fuente caída: Detalle > Notion > simular token inválido
await page.evaluate(() => { window.location.hash = 'detalle' })
await page.getByRole('tab', { name: 'Notion' }).click()
await page.getByRole('button', { name: 'Simular token inválido' }).click()
await page.waitForTimeout(300)
await page.evaluate(() => { window.location.hash = 'dashboard' })
await page.waitForTimeout(300)
await foto('05_fuente_notion_caida.png', { fullPage: true })
await foto('06_estado_fuentes_fallo.png', { clip: { x: 238, y: 510, width: 1042, height: 210 } })

await page.setViewportSize({ width: 390, height: 844 })
await page.waitForTimeout(300)
await foto('07_movil.png', { fullPage: true })
await browser.close()
console.log('ok')
