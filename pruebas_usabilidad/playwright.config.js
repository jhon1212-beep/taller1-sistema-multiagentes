/**
 * Pruebas de usabilidad y accesibilidad del frontend (atributo de calidad: usabilidad).
 *
 * Levanta la build de producción del frontend y ejecuta los casos contra ella.
 * Navegador: Chromium de Playwright; en equipos sin descarga se puede usar el
 * Edge instalado con NAVEGADOR=msedge.
 */
import { defineConfig, devices } from '@playwright/test'

const PUERTO = 4174
const URL_BASE = `http://localhost:${PUERTO}`
const canal = process.env.NAVEGADOR || undefined

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: 'resultados-playwright.json' }]],
  use: {
    baseURL: URL_BASE,
    ...devices['Desktop Chrome'],
    ...(canal ? { channel: canal } : {}),
  },
  webServer: {
    command: `npm --prefix ../frontend run build && npm --prefix ../frontend run preview -- --port ${PUERTO}`,
    url: URL_BASE,
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
