/**
 * HU-001 · Captura los estados del inicio de sesión para la documentación.
 *
 * No es una prueba: conduce la interfaz real y guarda una imagen por estado,
 * de modo que la evidencia del documento se pueda regenerar cuando la
 * pantalla cambie, en lugar de quedar desactualizada.
 *
 * Requiere el servidor levantado:  npm run preview -- --port 4173
 * Uso:                             node scripts/capturar-login.mjs
 */
import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const SALIDA = path.resolve(AQUI, '../../docs/sprint1/evidencias/login')
const BASE = process.env.URL_BASE ?? 'http://localhost:4173'

const CORREO = 'docente1@demo.test'
const CLAVE = 'DemoDocente2026!'

const ESTADOS = [
  {
    archivo: '01_formulario.png',
    descripcion: 'Formulario inicial, sin sesión',
    async preparar(page) {
      await page.goto(`${BASE}/`)
    },
  },
  {
    archivo: '02_campos_vacios.png',
    descripcion: 'Envío con los campos vacíos',
    async preparar(page) {
      await page.goto(`${BASE}/`)
      await page.getByRole('button', { name: 'Ingresar' }).click()
      await page.getByRole('alert').waitFor()
    },
  },
  {
    archivo: '03_credenciales_invalidas.png',
    descripcion: 'Contraseña incorrecta',
    async preparar(page) {
      await page.goto(`${BASE}/`)
      await page.getByLabel('Correo del docente').fill(CORREO)
      await page.getByLabel('Contraseña', { exact: true }).fill('clave-que-no-es')
      await page.getByRole('button', { name: 'Ingresar' }).click()
      await page.getByRole('alert').waitFor()
    },
  },
  {
    archivo: '04_acceso_bloqueado.png',
    descripcion: 'Intento de abrir una ruta privada sin sesión',
    async preparar(page) {
      await page.goto(`${BASE}/#dashboard`)
      await page.getByRole('alert').waitFor()
    },
  },
  {
    archivo: '05_sesion_iniciada.png',
    descripcion: 'Sesión iniciada: entra a Mis proyectos',
    async preparar(page) {
      await page.goto(`${BASE}/`)
      await page.getByLabel('Correo del docente').fill(CORREO)
      await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
      await page.getByRole('button', { name: 'Ingresar' }).click()
      await page.getByRole('heading', { name: 'Mis proyectos' }).waitFor()
    },
  },
]

const navegador = await chromium.launch()
try {
  await mkdir(SALIDA, { recursive: true })
  const contexto = await navegador.newContext({ viewport: { width: 1366, height: 900 } })

  for (const estado of ESTADOS) {
    const page = await contexto.newPage()
    await estado.preparar(page)
    await page.screenshot({ path: path.join(SALIDA, estado.archivo), fullPage: true })
    await page.close()
    console.log(`✔ ${estado.archivo}  —  ${estado.descripcion}`)
  }
} finally {
  await navegador.close()
}
console.log(`\nCapturas en ${SALIDA}`)
