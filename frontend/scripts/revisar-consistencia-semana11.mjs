/**
 * TA-024 · Revisión de consistencia de la interfaz del Sprint 2.
 * Recorre las pantallas con la API real, mide en el navegador los puntos de la lista de
 * verificación (tipografía, color de botón primario, radio de tarjeta, un solo h1, aviso
 * de conexión, desborde horizontal en móvil y escritorio) y toma capturas.
 * Requiere API y frontend como en capturar-semana11.mjs.
 * Uso: node scripts/revisar-consistencia-semana11.mjs
 */
import { chromium } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const BASE = process.env.URL_BASE ?? 'http://127.0.0.1:5173'
const SALIDA = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana11/ta024')
await mkdir(SALIDA, { recursive: true })

const browser = await chromium.launch({ channel: 'msedge' })
const medidas = []

async function medir(page, nombre, tam) {
  const m = await page.evaluate(() => {
    const cs = (el, p) => (el ? getComputedStyle(el)[p] : null)
    const h1 = document.querySelectorAll('h1')
    const btn = document.querySelector('main .btn:not(.btn-sec):not(.btn-danger)')
    const card = document.querySelector('.card')
    return {
      h1: h1.length,
      fuente: cs(document.body, 'fontFamily').split(',')[0].replace(/"/g, '').trim(),
      fuenteH1: cs(h1[0], 'fontFamily')?.split(',')[0].replace(/"/g, '').trim() ?? null,
      colorBoton: cs(btn, 'backgroundColor'),
      radioTarjeta: cs(card, 'borderRadius'),
      eyebrow: !!document.querySelector('.eyebrow'),
      bandaConexion: /Conectado al servidor/.test(document.body.innerText),
      desborde: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      menu: !!document.querySelector('nav[aria-label="Navegación docente"]'),
    }
  })
  medidas.push({ pantalla: nombre, ancho: tam, ...m })
}

for (const [tam, vp] of [['escritorio', { width: 1280, height: 800 }], ['móvil', { width: 375, height: 812 }]]) {
  const page = await browser.newPage({ viewport: vp })
  const foto = (n, o = {}) => page.screenshot({ path: path.join(SALIDA, `${tam === 'móvil' ? 'movil' : 'escritorio'}_${n}.png`), ...o })
  await page.goto(`${BASE}/#login`)
  await medir(page, 'Inicio de sesión', tam)
  await page.getByLabel('Correo del docente').fill('docente@upao.test')
  await page.getByLabel('Contraseña', { exact: true }).fill('Demo-2026')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await page.getByRole('heading', { name: 'Mis proyectos' }).waitFor()
  await page.getByText('Proyecto demo Grupo 8').first().waitFor()
  await medir(page, 'Mis proyectos', tam)

  await page.locator('tr, .card', { hasText: 'Proyecto demo Grupo 8' }).first().getByRole('button', { name: 'Ver proyecto' }).click()
  await page.getByRole('button', { name: 'Ver Dashboard' }).click()
  await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor()
  await page.locator('#dash-indicadores').waitFor()
  await medir(page, 'Dashboard', tam)
  await foto('dashboard', { fullPage: true })

  await page.getByRole('button', { name: /Ver detalle y evidencia/ }).first().click()
  await page.waitForSelector('#alerta-explicacion')
  await medir(page, 'Detalle de alerta', tam)
  await foto('alerta', { fullPage: true })
  await page.getByRole('button', { name: 'Volver al Dashboard' }).click()

  await page.getByRole('button', { name: 'Ver validación' }).click()
  await page.getByRole('heading', { name: 'Verificación de la aplicación' }).waitFor()
  await page.getByRole('heading', { name: 'Último resultado' }).waitFor()
  await medir(page, 'Validación web', tam)
  await foto('validacion', { fullPage: true })

  await page.goto(`${BASE}/#historial`)
  await page.getByRole('heading', { name: 'Comparación entre cortes' }).waitFor()
  await medir(page, 'Historial', tam)
  await foto('historial', { fullPage: true })
  await page.close()
}
await writeFile(path.join(SALIDA, 'mediciones.json'), JSON.stringify(medidas, null, 2), 'utf-8')
console.log(JSON.stringify(medidas.map(m => [m.ancho, m.pantalla, m.h1, m.fuente, m.colorBoton, m.radioTarjeta, m.desborde]), null, 0))
await browser.close()

