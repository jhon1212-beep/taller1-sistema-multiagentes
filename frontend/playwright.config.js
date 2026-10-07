/**
 * TA-008 · Configuración de las pruebas E2E
 *
 * Levanta la build de producción y ejecuta los casos contra ella, que es lo
 * más parecido a lo que verá el docente. Si el servidor ya está corriendo,
 * lo reutiliza en lugar de levantar otro.
 */
import { defineConfig, devices } from '@playwright/test'

const PUERTO = 4173
const URL_BASE = `http://localhost:${PUERTO}`

export default defineConfig({
  testDir: './e2e',
  // En CI no se permiten pruebas marcadas como only, y se reintenta una vez
  // para absorber lentitud del runner sin tapar un fallo real.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [['list'], ['junit', { outputFile: '../test-results/e2e.xml' }]]
    : [['list']],
  use: {
    baseURL: URL_BASE,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: `npm run build && npm run preview -- --port ${PUERTO}`,
    url: URL_BASE,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
