/**
 * TA-040 · Frontend conectado a la API real (backend FastAPI + PostgreSQL).
 *
 * Requisitos en la base: un docente (E2E_CORREO / E2E_CLAVE) con el proyecto
 * «Proyecto demo Grupo 8» y sus 3 fuentes con la referencia «dataset:1»
 * (scripts/seed_supervision_demo.py), y el backend con SUPERVISION_SOURCES=dataset.
 *
 *   CP-API1 · Inicio de sesión real y lista de proyectos del servidor.
 *   CP-API2 · «Ejecutar supervisión» corre los agentes y el Dashboard muestra I1–I4
 *             iguales a la hoja de TA-017 (40 %, 60 %, 4, 0) para el corte del 12/10/2026.
 *   CP-API3 · Las alertas del corte abren su detalle con regla, explicación y evidencia.
 *   CP-API4 · El Historial compara al menos 2 cortes y ofrece el reporte imprimible.
 *   CP-API5 · La pestaña Validación web muestra el último CP-17 y permite reejecutarlo.
 */
import { expect, test } from '@playwright/test'

const CORREO = process.env.E2E_CORREO ?? 'docente@upao.test'
const CLAVE = process.env.E2E_CLAVE ?? 'Demo-2026'
const PROYECTO = process.env.E2E_PROYECTO ?? 'Proyecto demo Grupo 8'

async function entrar(page) {
  await page.goto('/')
  await expect(page.getByText('Conectado al servidor.')).toBeVisible()
  await page.getByLabel('Correo del docente').fill(CORREO)
  await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible()
  await expect(page.getByText(PROYECTO).first()).toBeVisible()
}

async function abrirDashboard(page) {
  const fila = page.locator('tr, .card', { hasText: PROYECTO }).first()
  await fila.getByRole('button', { name: 'Ver proyecto' }).click()
  await page.getByRole('button', { name: 'Ver Dashboard' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
}

async function ejecutarCorte(page, dia) {
  await page.getByLabel('Fecha de corte').fill(dia)
  await page.getByRole('button', { name: 'Ejecutar supervisión' }).click()
  await expect(page.locator('.traza')).toContainText(`corte ${dia}`)
}

/** Registra un proyecto por el formulario (Drive solo si se indica) y vuelve a Mis proyectos. */
async function registrarProyecto(page, nombre, { drive = '' } = {}) {
  await page.getByRole('button', { name: '+ Registrar proyecto' }).click()
  await page.getByLabel('Nombre del proyecto').fill(nombre)
  await page.getByLabel('Curso').fill('Taller Integrador 1')
  await page.getByLabel('Fecha de inicio').fill('2026-09-21')
  await page.getByLabel('Fecha de fin').fill('2026-12-04')
  await page.getByLabel(/Integrantes del equipo/).fill('Integrante 1, Integrante 2')
  await page.getByLabel('Repositorio de GitHub').fill('https://github.com/octocat/Hello-World')
  await page.getByLabel('Base de tareas de Notion').fill('https://www.notion.so/base-demo-0123456789abcdef0123456789abcdef')
  if (drive) await page.getByLabel(/Carpeta de Google Drive/).fill(drive)
  await page.getByLabel('URL pública de la aplicación').fill('https://example.com')
  await page.getByLabel('Elemento a verificar (selector CSS)').fill('h1')
  await page.getByRole('button', { name: 'Guardar proyecto' }).click()
}

const tarjeta = (page, etiqueta) => page.locator('.stat', { hasText: etiqueta })

test('CP-API1 · inicia sesión contra el backend y lista los proyectos reales', async ({ page }) => {
  await entrar(page)
  await page.screenshot({ path: 'test-results-api/01_proyectos.png', fullPage: true })
})

test('CP-API2 · ejecutar la supervisión guarda el corte y muestra I1–I4 de TA-017', async ({ page }) => {
  await entrar(page)
  await abrirDashboard(page)
  await ejecutarCorte(page, '2026-10-06')
  await ejecutarCorte(page, '2026-10-12')

  await expect(page.getByText('12/10/2026 · 23:59 (hora de Lima)').first()).toBeVisible()
  await expect(tarjeta(page, 'Tareas completadas (I1)')).toContainText('40 %')
  await expect(tarjeta(page, 'Tareas pendientes (I2)')).toContainText('60 %')
  await expect(tarjeta(page, 'Tareas vencidas (I3)')).toContainText('4')
  await expect(tarjeta(page, 'Días sin actividad (I4)')).toContainText('0')
  await expect(page.locator('.traza')).toContainText('PostgreSQL:')
  await page.screenshot({ path: 'test-results-api/02_dashboard.png', fullPage: true })
})

test('CP-API3 · cada alerta abre su detalle con regla, explicación y evidencia', async ({ page }) => {
  await entrar(page)
  await abrirDashboard(page)
  await expect(page.getByRole('heading', { name: /^Alertas · \d+$/ })).toBeVisible()
  await page.getByRole('button', { name: /^R1 \(/ }).click()
  await page.getByRole('button', { name: /Ver detalle y evidencia: R1/ }).first().click()

  await expect(page.getByRole('heading', { name: '¿Por qué se generó?' })).toBeVisible()
  await expect(page.getByText('Regla R1').first()).toBeVisible()
  await expect(page.getByText('Explicación: plantilla')).toBeVisible()
  await expect(page.getByText('Tarea:')).toBeVisible()
  await expect(page.getByText('no asigna notas')).toBeVisible()
  await page.screenshot({ path: 'test-results-api/03_alerta.png', fullPage: true })
})

test('CP-API4 · el historial compara cortes y ofrece el reporte imprimible', async ({ page }) => {
  await entrar(page)
  await abrirDashboard(page)
  await page.getByRole('button', { name: 'Ver historial de cortes' }).click()
  await expect(page.getByRole('heading', { name: 'Historial de supervisión' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Comparación entre cortes' })).toBeVisible()
  await expect(page.getByRole('cell', { name: '06/10/2026' }).first()).toBeVisible()
  await expect(page.getByRole('cell', { name: '12/10/2026' }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: 'Imprimir reporte' })).toBeEnabled()
  await page.screenshot({ path: 'test-results-api/04_historial.png', fullPage: true })
  await page.emulateMedia({ media: 'print' })
  await page.screenshot({ path: 'test-results-api/05_reporte_impresion.png', fullPage: true })
})

test('CP-API5 · la validación web muestra y reejecuta CP-17', async ({ page }) => {
  await entrar(page)
  await abrirDashboard(page)
  await page.getByRole('button', { name: 'Ver validación' }).click()
  await expect(page.getByRole('heading', { name: 'Verificación de la aplicación' })).toBeVisible()
  await expect(page.getByText('No evalúa la calidad global del código')).toBeVisible()
  await page.getByRole('button', { name: 'Ejecutar validación' }).click()
  await expect(page.getByRole('heading', { name: 'Último resultado' })).toBeVisible({ timeout: 110_000 })
  await expect(page.locator('.validacion-resultado .pill').first()).toHaveText(/PASS|FAIL/)
  await page.screenshot({ path: 'test-results-api/06_validacion.png', fullPage: true })
})

test('CP-API6 · un proyecto sin carpeta de Drive se registra y la muestra como no configurada', async ({ page }) => {
  const nombre = `Proyecto sin Drive ${Date.now()}`
  await entrar(page)
  // La carpeta de Google Drive queda vacía a propósito: es opcional.
  await registrarProyecto(page, nombre)

  const tarjetaProyecto = page.locator('.card', { hasText: nombre }).first()
  await expect(tarjetaProyecto).toBeVisible()
  await expect(tarjetaProyecto.getByText('Google Drive')).toHaveCount(0)
  await tarjetaProyecto.getByRole('button', { name: 'Ver proyecto' }).click()
  await expect(page.getByText('No configurada (opcional)')).toBeVisible()
  await expect(page.locator('.stat', { hasText: 'Fuentes previstas' })).toContainText('2')
  await page.screenshot({ path: 'test-results-api/07_proyecto_sin_drive.png', fullPage: true })

  // Se desactiva para no dejar el proyecto de prueba activo en la lista del docente.
  await page.getByRole('button', { name: /Mis proyectos/ }).first().click()
  await page.locator('.card', { hasText: nombre }).first().getByRole('button', { name: 'Desactivar' }).click()
})

test('CP-API7 · commits, tareas y documentos tienen un botón para abrir el original', async ({ page }) => {
  // Se simulan las 3 listas con identificadores reales: el proyecto demo usa el
  // dataset de TA-017, cuyos ids no existen en GitHub, Notion ni Drive.
  const sha = '0123456789abcdef0123456789abcdef01234567'
  const tareaId = '2a1b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d'
  const archivoId = '1AbCdEfGhIjKlMnOpQrStUvWxYz012345'
  await page.route('**/proyectos/*/commits', r => r.fulfill({ json: {
    proyecto_id: 1, fuente: 'github', estado_fuente: 'ok', ultima_extraccion: null, total: 1,
    items: [{ sha, autor: 'Integrante 1', fecha: '2026-10-12T10:00:00Z', mensaje: 'feat: login' }] } }))
  await page.route('**/proyectos/*/tareas', r => r.fulfill({ json: {
    proyecto_id: 1, fuente: 'notion', estado: 'ok', error: null, total: 1,
    resumen: { listo: 0, en_curso: 1, sin_empezar: 0, sin_responsable: 0 },
    tareas: [{ id: tareaId, tarea: 'Pantalla de login', responsable: 'Integrante 1', estado: 'En curso',
      fecha_limite: '2026-10-20', editada: '2026-10-12T10:00:00Z' }] } }))
  await page.route('**/proyectos/*/documentos', r => r.fulfill({ json: {
    proyecto_id: 1, fuente: 'drive', estado_fuente: 'ok', ultima_extraccion: null, total: 1,
    items: [{ id: archivoId, nombre: 'Informe final.pdf', ultimo_editor: 'Integrante 2',
      fecha: '2026-10-11T09:00:00Z', tipo: 'application/pdf' }] } }))

  // Proyecto con enlaces reales: con ellos se arma la URL del commit (repositorio) y de los demás.
  const nombre = `Proyecto con enlaces ${Date.now()}`
  await entrar(page)
  await registrarProyecto(page, nombre, { drive: 'https://drive.google.com/drive/folders/carpeta-demo' })
  const tarjetaProyecto = page.locator('.card', { hasText: nombre }).first()
  await tarjetaProyecto.getByRole('button', { name: 'Ver proyecto' }).click()

  await page.getByRole('tab', { name: 'GitHub' }).click()
  await expect(page.getByRole('link', { name: 'Abrir el commit 0123456 en GitHub' }))
    .toHaveAttribute('href', `https://github.com/octocat/Hello-World/commit/${sha}`)

  await page.getByRole('tab', { name: 'Notion' }).click()
  await expect(page.getByRole('link', { name: 'Abrir la tarea «Pantalla de login» en Notion' }))
    .toHaveAttribute('href', `https://www.notion.so/${tareaId.replace(/-/g, '')}`)

  await page.getByRole('tab', { name: 'Google Drive' }).click()
  const abrir = page.getByRole('link', { name: 'Abrir «Informe final.pdf» en Google Drive' })
  await expect(abrir).toHaveAttribute('href', `https://drive.google.com/file/d/${archivoId}/view`)
  await expect(abrir).toHaveAttribute('target', '_blank')
  await expect(page.getByRole('cell', { name: 'PDF', exact: true })).toBeVisible()
  await page.screenshot({ path: 'test-results-api/08_abrir_documento_drive.png', fullPage: true })

  await page.getByRole('button', { name: /Mis proyectos/ }).first().click()
  await page.locator('.card', { hasText: nombre }).first().getByRole('button', { name: 'Desactivar' }).click()
})

test('CP-API8 · R5 muestra el motivo de la incoherencia y abre el commit en GitHub', async ({ page }) => {
  // Se simula un corte con una alerta R5: el dataset de TA-017 no trae los archivos de cada commit.
  const sha = 'fedcba9876543210fedcba9876543210fedcba98'
  const motivo = 'El mensaje «test: pruebas del login» dice agregar pruebas, pero no se modificó ningún ' +
    'archivo de pruebas. Archivos modificados: README.md.'
  const dia = '2026-10-12'
  await page.route('**/proyectos/*/historial', r => r.fulfill({ json: {
    proyecto_id: 1, total_cortes: 1,
    cortes: [{ fecha_corte: dia, indicadores: { I1: 50, I2: 50, I3: 0, I4: 1 }, total_alertas: 1,
      alertas_por_regla: { R5: 1 }, validacion: null }] } }))
  await page.route('**/proyectos/*/indicadores**', r => r.fulfill({ json: {
    proyecto_id: 1, fecha_corte: dia, indicadores: { I1: 50, I2: 50, I3: 0, I4: 1 },
    estado_fuentes: { github: 'ok', notion: 'ok', drive: 'no_configurada' } } }))
  await page.route('**/proyectos/*/alertas**', r => r.fulfill({ json: {
    proyecto_id: 1, fecha_corte: dia, total: 1,
    alertas: [{ regla: 'R5', fuente: 'github', evidencia_ids: [sha], origen_explicacion: 'gemini',
      explicacion: `${motivo}\n\nConviene abrir el commit y comparar su mensaje con los cambios.`,
      evidencia: { fuente: 'github', id_externo: sha, autor: 'Integrante 1', fecha: '2026-10-12T10:00:00Z',
        descripcion: 'test: pruebas del login', proyecto_id: 1 } }] } }))

  const nombre = `Proyecto R5 ${Date.now()}`
  await entrar(page)
  await registrarProyecto(page, nombre)
  await page.locator('.card', { hasText: nombre }).first().getByRole('button', { name: 'Ver proyecto' }).click()
  await page.getByRole('button', { name: 'Ver Dashboard' }).click()

  await expect(page.getByRole('button', { name: 'R5 (1)' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Commit a revisar' })).toBeVisible()
  await page.getByRole('button', { name: /Ver detalle y evidencia: R5/ }).click()

  await expect(page.locator('.explicacion')).toContainText(motivo)
  await expect(page.getByText('No prueba que el estudiante haya mentido')).toBeVisible()
  await expect(page.getByRole('link', { name: /Abrir la evidencia en GitHub/ }))
    .toHaveAttribute('href', `https://github.com/octocat/Hello-World/commit/${sha}`)
  await page.screenshot({ path: 'test-results-api/09_alerta_r5_commit.png', fullPage: true })

  await page.getByRole('button', { name: /Mis proyectos/ }).first().click()
  await page.locator('.card', { hasText: nombre }).first().getByRole('button', { name: 'Desactivar' }).click()
})
