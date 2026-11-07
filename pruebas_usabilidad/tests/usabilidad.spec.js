/**
 * Pruebas de usabilidad (Mondragón) · frontend del docente
 *
 *   U1  Capturas de todas las pantallas en escritorio, tableta y móvil
 *   U2  Accesibilidad automática (axe-core, WCAG 2.1 A y AA) por pantalla
 *   U3  Navegación por teclado y foco visible
 *   U4  Responsive: sin desplazamiento horizontal en móvil, 320 px y zoom 200 %
 *   U5  Tamaño de los objetivos táctiles
 *   U6  Tareas del docente (éxito, acciones y tiempo)
 *   U7  Mensajes de error y retroalimentación del formulario
 *   U8  Metadatos de la página (idioma, título, encabezados)
 *
 * Las medidas se guardan como JSON en docs/usabilidad/resultados y las capturas en
 * docs/usabilidad/capturas. Esto NO sustituye la prueba con usuarios reales: para
 * eso está el guion en docs/usabilidad/guion-usuarios.md.
 */
import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const AQUI = path.dirname(fileURLToPath(import.meta.url))
const SALIDA = process.env.SALIDA_USABILIDAD ?? path.resolve(AQUI, '../../docs/usabilidad')
const CAP = path.join(SALIDA, 'capturas')
const RES = path.join(SALIDA, 'resultados')
fs.mkdirSync(CAP, { recursive: true })
fs.mkdirSync(RES, { recursive: true })

const CORREO = 'docente1@demo.test'
const CLAVE = 'DemoDocente2026!'

const PANTALLAS = [
  ['login', null], ['proyectos', 'proyectos'], ['nuevo', 'nuevo'], ['detalle', 'detalle'],
  ['dashboard', 'dashboard'], ['alerta', 'alerta'], ['historial', 'historial'], ['sistema', 'sistema'],
]
const VIEWPORTS = {
  escritorio: { width: 1366, height: 850 },
  tableta: { width: 768, height: 1024 },
  movil: { width: 375, height: 812 },
}

const guardar = (nombre, datos) =>
  fs.writeFileSync(path.join(RES, `${nombre}.json`), JSON.stringify(datos, null, 2), 'utf-8')

async function entrar(page) {
  await page.goto('/')
  await page.getByLabel('Correo del docente').fill(CORREO)
  await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible()
}

async function ir(page, hash) {
  await page.evaluate(h => { window.location.hash = h }, hash)
  await page.waitForTimeout(300)
}

/** Abre una pantalla (con sesión si hace falta). */
async function abrir(page, [nombre, hash]) {
  if (nombre === 'login') await page.goto('/')
  else await ir(page, hash)
}

test.describe('U1 · Capturas por pantalla y dispositivo', () => {
  for (const [vp, tam] of Object.entries(VIEWPORTS)) {
    test(`capturas en ${vp}`, async ({ page }) => {
      await page.setViewportSize(tam)
      await page.goto('/')
      await page.screenshot({ path: path.join(CAP, `${vp}_login.png`), fullPage: true })
      await entrar(page)
      for (const pantalla of PANTALLAS.slice(1)) {
        await abrir(page, pantalla)
        await page.screenshot({ path: path.join(CAP, `${vp}_${pantalla[0]}.png`), fullPage: true })
      }
    })
  }
})

test.describe('U2 · Accesibilidad automática (axe-core)', () => {
  test('todas las pantallas en escritorio', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.escritorio)
    const informe = []
    await page.goto('/')
    for (const pantalla of PANTALLAS) {
      if (pantalla[0] === 'login') await page.goto('/')
      else {
        if (!(await page.getByRole('navigation').count())) await entrar(page)
        await ir(page, pantalla[1])
      }
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
      informe.push({
        pantalla: pantalla[0],
        reglas_aprobadas: r.passes.length,
        violaciones: r.violations.map(v => ({
          id: v.id, impacto: v.impact, ayuda: v.help, elementos: v.nodes.length,
          ejemplo: v.nodes[0]?.target?.join(' '), html: v.nodes[0]?.html?.slice(0, 160),
        })),
      })
    }
    guardar('axe', informe)
    const graves = informe.flatMap(i => i.violaciones.filter(v => ['critical', 'serious'].includes(v.impacto)))
    expect.soft(graves, 'violaciones críticas o serias de accesibilidad').toEqual([])
  })
})

test.describe('U3 · Teclado y foco visible', () => {
  test('recorrido con Tab en el login y en Mis proyectos', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.escritorio)
    const leer = () => page.evaluate(() => {
      const el = document.activeElement
      const s = getComputedStyle(el)
      return {
        etiqueta: el.tagName.toLowerCase(),
        texto: (el.getAttribute('aria-label') || el.innerText || el.getAttribute('name') || el.id || '').trim().slice(0, 40),
        foco_visible: (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none',
      }
    })
    const recorrer = async n => {
      const pasos = []
      for (let i = 0; i < n; i++) { await page.keyboard.press('Tab'); pasos.push(await leer()) }
      return pasos
    }
    await page.goto('/')
    const login = await recorrer(5)
    await page.getByLabel('Correo del docente').focus()
    await page.keyboard.type(CORREO)
    await page.keyboard.press('Tab')
    await page.keyboard.type(CLAVE)
    await page.keyboard.press('Enter') // enviar con Enter
    const entroConEnter = await page.getByRole('heading', { name: 'Mis proyectos' }).isVisible()
    const proyectos = await recorrer(8)
    guardar('teclado', { login, entro_con_enter: entroConEnter, proyectos })
    expect.soft(entroConEnter, 'el formulario se envía con Enter').toBe(true)
    expect.soft([...login, ...proyectos].filter(p => p.etiqueta !== 'body' && !p.foco_visible), 'elementos sin foco visible').toEqual([])
  })
})

test.describe('U4 · Responsive', () => {
  const anchos = { movil_375: { width: 375, height: 812 }, movil_320: { width: 320, height: 640 }, zoom_200: { width: 683, height: 425 } }
  test('sin desplazamiento horizontal', async ({ page }) => {
    const informe = []
    for (const [nombre, tam] of Object.entries(anchos)) {
      await page.setViewportSize(tam)
      await entrar(page)
      for (const pantalla of PANTALLAS.slice(1)) {
        await abrir(page, pantalla)
        const m = await page.evaluate(() => ({ ancho_documento: document.documentElement.scrollWidth, ancho_ventana: window.innerWidth }))
        const desborda = m.ancho_documento > m.ancho_ventana + 1
        informe.push({ vista: nombre, pantalla: pantalla[0], ...m, desborda })
        if (desborda) await page.screenshot({ path: path.join(CAP, `desborde_${nombre}_${pantalla[0]}.png`) })
      }
    }
    guardar('responsive', informe)
    expect.soft(informe.filter(i => i.desborda), 'pantallas con desplazamiento horizontal').toEqual([])
  })
})

test.describe('U5 · Objetivos táctiles', () => {
  test('tamaño de botones, enlaces y campos en móvil', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.movil)
    await entrar(page)
    const informe = []
    for (const pantalla of PANTALLAS.slice(1)) {
      await abrir(page, pantalla)
      const objetivos = await page.evaluate(() =>
        [...document.querySelectorAll('button, a[href], input, select, textarea, [role=tab]')]
          .filter(e => e.offsetParent !== null)
          .map(e => {
            const r = e.getBoundingClientRect()
            return { elemento: e.tagName.toLowerCase(), texto: (e.innerText || e.getAttribute('aria-label') || e.name || '').trim().slice(0, 30), ancho: Math.round(r.width), alto: Math.round(r.height) }
          }))
      informe.push({
        pantalla: pantalla[0], total: objetivos.length,
        menores_24px: objetivos.filter(o => o.ancho < 24 || o.alto < 24),
        menores_44px: objetivos.filter(o => o.ancho < 44 || o.alto < 44).length,
      })
    }
    guardar('objetivos_tactiles', informe)
    // WCAG 2.2 · 2.5.8 (AA): mínimo 24×24 px
    expect.soft(informe.flatMap(i => i.menores_24px), 'objetivos menores a 24 px').toEqual([])
  })
})

test.describe('U6 · Tareas del docente', () => {
  test('T1-T5: éxito, acciones y tiempo', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.escritorio)
    page.setDefaultTimeout(5000)
    const tareas = []
    async function medir(id, descripcion, fn) {
      const t0 = Date.now()
      let acciones = 0
      const a = async promesa => { acciones++; return promesa }
      let exito = true, error = ''
      try { await fn(a) } catch (e) { exito = false; error = String(e.message).split('\n')[0] }
      tareas.push({ id, descripcion, exito, acciones, tiempo_ms: Date.now() - t0, error })
    }

    await medir('T1', 'Iniciar sesión y llegar a Mis proyectos', async a => {
      await page.goto('/')
      await a(page.getByLabel('Correo del docente').fill(CORREO))
      await a(page.getByLabel('Contraseña', { exact: true }).fill(CLAVE))
      await a(page.getByRole('button', { name: 'Ingresar' }).click())
      await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible({ timeout: 3000 })
    })
    await medir('T2', 'Registrar un proyecto nuevo', async a => {
      await a(page.getByRole('button', { name: /Registrar proyecto|Nuevo/i }).first().click())
      await a(page.getByLabel('Nombre del proyecto').fill('Proyecto de usabilidad'))
      await a(page.getByLabel('Curso', { exact: true }).fill('Taller Integrador 1'))
      await a(page.getByLabel('Fecha de inicio').fill('2026-08-01'))
      await a(page.getByLabel('Fecha de fin').fill('2026-12-15'))
      await a(page.getByLabel(/Integrantes del equipo/).fill('Ana, Luis'))
      await a(page.getByLabel('Repositorio de GitHub').fill('https://github.com/org/repo'))
      await a(page.getByLabel('Base de tareas de Notion').fill('https://notion.so/base'))
      await a(page.getByLabel('Carpeta de Google Drive').fill('https://drive.google.com/carpeta'))
      await a(page.getByLabel('URL pública de la aplicación').fill('https://ejemplo.test'))
      await a(page.getByLabel(/Elemento a verificar/).fill('h1'))
      await a(page.getByRole('button', { name: 'Guardar proyecto' }).click())
      await expect(page.getByRole('status')).toContainText('Proyecto guardado', { timeout: 3000 })
    })
    await medir('T3', 'Abrir el detalle de un proyecto y volver', async a => {
      await a(page.getByRole('button', { name: /Ver proyecto/i }).first().click())
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await a(page.getByRole('button', { name: 'Mis proyectos', exact: true }).last().click())
      await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible({ timeout: 3000 })
    })
    await medir('T4', 'Ir al Dashboard y simular una supervisión', async a => {
      await a(page.getByRole('button', { name: 'Dashboard', exact: true }).click())
      await a(page.getByRole('button', { name: 'Simular supervisión' }).click())
      await expect(page.getByText('Supervisor: ejecución simulada iniciada')).toBeVisible({ timeout: 3000 })
    })
    await medir('T5', 'Abrir el detalle de una alerta', async a => {
      await a(page.getByRole('button', { name: 'Ver detalle y evidencia' }).first().click())
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 3000 })
    })
    await medir('T6', 'Cerrar sesión', async a => {
      await a(page.getByRole('button', { name: 'Cerrar sesión' }).click())
      await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible({ timeout: 3000 })
    })

    await page.screenshot({ path: path.join(CAP, 'tareas_estado_final.png') })
    guardar('tareas', tareas)
    expect.soft(tareas.filter(t => !t.exito), 'tareas no completadas').toEqual([])
  })
})

test.describe('U7 · Errores y retroalimentación', () => {
  test('formulario vacío, fechas inválidas y URL inválida', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.escritorio)
    await entrar(page)
    await ir(page, 'nuevo')
    const casos = []
    const probar = async (caso, preparar) => {
      await preparar()
      await page.getByRole('button', { name: 'Guardar proyecto' }).click()
      const alerta = page.getByRole('alert')
      const visible = await alerta.isVisible()
      casos.push({ caso, mensaje_visible: visible, mensaje: visible ? (await alerta.innerText()).trim() : '', es_alert: visible })
      if (caso === 'Formulario vacío') await page.screenshot({ path: path.join(CAP, 'error_formulario_vacio.png') })
    }
    await probar('Formulario vacío', async () => {})
    await probar('Fecha de fin anterior al inicio', async () => {
      await page.getByLabel('Nombre del proyecto').fill('X')
      await page.getByLabel('Curso', { exact: true }).fill('X')
      await page.getByLabel('Fecha de inicio').fill('2026-12-15')
      await page.getByLabel('Fecha de fin').fill('2026-08-01')
      await page.getByLabel(/Integrantes del equipo/).fill('Ana')
      await page.getByLabel('Repositorio de GitHub').fill('https://github.com/o/r')
      await page.getByLabel('Base de tareas de Notion').fill('https://notion.so/b')
      await page.getByLabel('Carpeta de Google Drive').fill('https://drive.google.com/c')
      await page.getByLabel('URL pública de la aplicación').fill('https://e.test')
      await page.getByLabel(/Elemento a verificar/).fill('h1')
    })
    await probar('URL inválida', async () => {
      await page.getByLabel('Fecha de fin').fill('2026-12-20')
      await page.getByLabel('URL pública de la aplicación').fill('no-es-una-url')
    })
    const ancho = await page.evaluate(() => document.querySelectorAll('[aria-invalid="true"]').length)
    guardar('errores_formulario', { casos, campos_marcados_aria_invalid: ancho })
    expect.soft(casos.filter(c => !c.mensaje_visible), 'casos sin mensaje de error').toEqual([])
  })
})

test.describe('U8 · Metadatos y estructura', () => {
  test('idioma, título y encabezados por pantalla', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.escritorio)
    await page.goto('/')
    const informe = []
    for (const pantalla of PANTALLAS) {
      if (pantalla[0] === 'login') await page.goto('/')
      else { if (!(await page.getByRole('navigation').count())) await entrar(page); await ir(page, pantalla[1]) }
      informe.push(await page.evaluate(nombre => ({
        pantalla: nombre,
        lang: document.documentElement.lang,
        titulo_documento: document.title,
        h1: document.querySelectorAll('h1').length,
        h2: document.querySelectorAll('h2').length,
        landmarks_main: document.querySelectorAll('main, [role=main]').length,
        imagenes_sin_alt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
      }), pantalla[0]))
    }
    guardar('metadatos', informe)
    expect.soft(informe.filter(i => i.h1 !== 1), 'pantallas sin exactamente un h1').toEqual([])
    expect.soft(new Set(informe.map(i => i.titulo_documento)).size, 'el título del documento no cambia entre pantallas').toBeGreaterThan(1)
  })
})
