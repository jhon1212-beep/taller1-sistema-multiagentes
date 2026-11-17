/**
 * TA-031 · Capturas «después» de los ajustes de usabilidad (semana 12).
 * Uso (con el frontend ya compilado y sirviéndose en el 4174):
 *   NAVEGADOR=msedge node capturas_ta031.mjs <carpeta_de_salida>
 */
import { chromium } from '@playwright/test'
import path from 'node:path'
import fs from 'node:fs'

const salida = path.resolve(process.argv[2] ?? '../docs/sprint2/evidencias/semana12_mondragon/capturas')
fs.mkdirSync(salida, { recursive: true })
const b = await chromium.launch({ channel: process.env.NAVEGADOR || undefined })

async function sesion(ancho, alto) {
  const p = await (await b.newContext({ viewport: { width: ancho, height: alto } })).newPage()
  await p.goto('http://localhost:4174/')
  await p.getByLabel('Correo del docente').fill('docente1@demo.test')
  await p.getByLabel('Contraseña', { exact: true }).fill('DemoDocente2026!')
  await p.getByRole('button', { name: 'Ingresar' }).click()
  return p
}
const ir = async (p, h) => { await p.evaluate(x => { location.hash = x }, h); await p.waitForTimeout(350) }

// 1. Formulario vacío: todos los errores a la vez, campos marcados y foco en el primero
let p = await sesion(1366, 850)
await ir(p, 'nuevo')
await p.getByRole('button', { name: 'Guardar proyecto' }).click()
await p.waitForTimeout(300)
await p.screenshot({ path: path.join(salida, 'ta031_form_errores_completa.png'), fullPage: true })

// 2. Detalle a 320 px (antes desbordaba 21 px) con el menú a la vista
p = await sesion(320, 640)
await ir(p, 'detalle')
await p.screenshot({ path: path.join(salida, 'ta031_detalle_320.png') })

// 3. Dashboard en móvil con la ayuda de un indicador abierta (antes desbordaba 46 px)
p = await sesion(375, 812)
await ir(p, 'dashboard')
await p.getByRole('button', { name: /Cómo se calcula/ }).first().focus()
await p.waitForTimeout(200)
await p.screenshot({ path: path.join(salida, 'ta031_dashboard_movil_ayuda.png') })

// 4. Pestaña del navegador: título por pantalla (se guarda como texto)
p = await sesion(1366, 850)
const titulos = {}
for (const h of ['proyectos', 'nuevo', 'detalle', 'dashboard', 'alerta', 'historial', 'sistema']) {
  await ir(p, h); titulos[h] = await p.title()
}
fs.writeFileSync(path.join(salida, '..', 'resultados', 'ta031_titulos.json'), JSON.stringify(titulos, null, 2))
await b.close()
