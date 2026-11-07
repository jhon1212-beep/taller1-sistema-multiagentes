/**
 * TA-040 · Pruebas E2E del frontend conectado a la API real.
 *
 * A diferencia de playwright.config.js (modo demostración), aquí la build se
 * hace con VITE_API_URL y las pruebas inician sesión con un docente real.
 *
 *   E2E_API_URL   URL del backend (por defecto http://localhost:8000; en Render, su URL)
 *   E2E_FRONT_URL si se define, se prueba esa URL (por ejemplo, la de Netlify) sin build local
 *   E2E_CORREO    correo del docente de prueba
 *   E2E_CLAVE     contraseña del docente de prueba
 *
 * Uso:  npx playwright test -c playwright.api.config.js
 */
import { defineConfig, devices } from '@playwright/test'

const PUERTO = 4174
const API = process.env.E2E_API_URL ?? 'http://localhost:8000'
const FRONT = process.env.E2E_FRONT_URL

export default defineConfig({
  testDir: './e2e-api',
  // El backend gratuito puede tardar hasta 1 minuto en despertar.
  timeout: 120_000,
  expect: { timeout: 30_000 },
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report-api', open: 'never' }]],
  use: {
    baseURL: FRONT ?? `http://localhost:${PUERTO}`,
    screenshot: 'on',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: FRONT
    ? undefined
    : {
        command: `npx vite build && npx vite preview --port ${PUERTO}`,
        url: `http://localhost:${PUERTO}`,
        reuseExistingServer: false,
        timeout: 120_000,
        env: { VITE_API_URL: API },
      },
})
