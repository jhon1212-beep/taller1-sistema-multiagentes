/**
 * HU-008 · Configuración del reporte Playwright de la consulta de validaciones (CP-17).
 *
 * No arranca nada: necesita la API en marcha (API_URL) con PostgreSQL y el ejecutor
 * local de validaciones (E2E_EJECUTOR=local en el servidor). Ver consulta-validaciones.spec.js.
 * Navegador: Chromium de Playwright, o el instalado con NAVEGADOR=msedge.
 */
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  testMatch: 'consulta-validaciones.spec.js',
  timeout: 120_000,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: process.env.API_URL ?? 'http://127.0.0.1:8000',
    ...devices['Desktop Chrome'],
    ...(process.env.NAVEGADOR ? { channel: process.env.NAVEGADOR } : {}),
  },
})
