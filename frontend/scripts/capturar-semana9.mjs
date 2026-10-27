/**
 * Semana 9 · Captura las pantallas para TA-011 (antes/después) y TA-020.
 *
 * Uso:  node scripts/capturar-semana9.mjs <carpeta> [rutas separadas por coma]
 * Requiere el servidor de desarrollo en URL_BASE (por defecto :5173).
 */
import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5173'
const carpeta = process.argv[2] ?? 'antes'
const SALIDA = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana9', carpeta)

const PANTALLAS = [
  ['01_login', 'login'],
  ['02_mis_proyectos', 'proyectos'],
  ['03_formulario_proyecto', 'nuevo'],
  ['04_detalle_proyecto', 'detalle'],
  ['05_dashboard', 'dashboard'],
  ['06_detalle_alerta', 'alerta'],
  ['07_historial', 'historial'],
  ['08_sistema_visual', 'sistema'],
]

await mkdir(SALIDA, { recursive: true })
const browser = await chromium.launch({ channel: 'msedge' })
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })

await page.goto(`${BASE}/#login`)
await page.getByLabel('Correo del docente').fill('docente1@demo.test')
await page.locator('input[type=password]').fill('DemoDocente2026!')
await page.locator('input[type=password]').press('Enter')
await page.waitForSelector('nav[aria-label="Navegación docente"]')

for (const [archivo, ruta] of PANTALLAS) {
  if (ruta === 'login') continue
  await page.evaluate(r => { window.location.hash = r }, ruta)
  await page.waitForTimeout(300)
  await page.screenshot({ path: path.join(SALIDA, `${archivo}.png`), fullPage: true })
  console.log('ok', archivo)
}
// Login se captura al final, ya sin sesión
await page.getByRole('button', { name: 'Cerrar sesión' }).click()
await page.waitForTimeout(300)
await page.screenshot({ path: path.join(SALIDA, '01_login.png'), fullPage: true })
console.log('ok 01_login')
await browser.close()
