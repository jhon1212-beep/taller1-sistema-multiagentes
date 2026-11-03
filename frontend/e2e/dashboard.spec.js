/**
 * HU-006 · HU-007 · Pruebas E2E del Dashboard (indicadores y alertas)
 *
 *   - Los cuatro indicadores I1–I4 coinciden con lo que calcula el motor (TA-019).
 *   - Cada indicador explica su fórmula y la fecha de corte, con ratón y con teclado.
 *   - El proyecto «Biblioteca digital» muestra las cuatro reglas R1–R4.
 *   - Cada alerta abre su detalle con la explicación y la evidencia de origen.
 *
 * Los textos de las cifras salen de src/datos/demo_supervision.js, que genera
 * backend/scripts/generar_demo_supervision.py; tests/unit/test_demo_supervision_frontend.py
 * comprueba que ese archivo coincide con el motor.
 */
import { expect, test } from '@playwright/test'

async function entrar(page) {
  await page.goto('/')
  await page.getByLabel('Correo del docente').fill('docente1@demo.test')
  await page.getByLabel('Contraseña', { exact: true }).fill('DemoDocente2026!')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible()
}

async function dashboardDe(page, indice) {
  await page.getByRole('button', { name: 'Ver proyecto' }).nth(indice).click()
  await page.getByRole('button', { name: 'Ver Dashboard' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
}

const tarjeta = (page, etiqueta) => page.locator('.stat', { hasText: etiqueta })

test.describe('HU-006 · Indicadores I1–I4', () => {
  test.beforeEach(async ({ page }) => {
    await entrar(page)
    await dashboardDe(page, 0)
  })

  test('CP-D1 · muestra I1–I4 del proyecto 1 con los valores del motor', async ({ page }) => {
    await expect(tarjeta(page, 'Tareas completadas (I1)')).toContainText('40 %')
    await expect(tarjeta(page, 'Tareas pendientes (I2)')).toContainText('60 %')
    await expect(tarjeta(page, 'Tareas vencidas (I3)')).toContainText('4')
    await expect(tarjeta(page, 'Días sin actividad (I4)')).toContainText('0')
    await expect(page.getByText('13/10/2026 04:59 UTC').first()).toBeVisible()
  })

  test('CP-D2 · la ayuda de I1 explica la fórmula y la fecha de corte', async ({ page }) => {
    await page.getByRole('button', { name: /Cómo se calcula: I1/ }).hover()
    const ayuda = page.getByRole('tooltip').filter({ hasText: 'I1 = tareas' })
    await expect(ayuda).toBeVisible()
    await expect(ayuda).toContainText('«Listo» ÷ total de tareas × 100')
    await expect(ayuda).toContainText('8 de 20 tareas')
    await expect(ayuda).toContainText('Fecha de corte: 13/10/2026 04:59 UTC')
  })

  test('CP-D3 · la ayuda se abre con el teclado y se cierra con Esc', async ({ page }) => {
    const boton = page.getByRole('button', { name: /Cómo se calcula: I3/ })
    await boton.focus()
    const ayuda = page.getByRole('tooltip').filter({ hasText: 'I3 = tareas' })
    await expect(ayuda).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(ayuda).toBeHidden()
    await expect(boton).toBeFocused()
  })

  test('CP-D4 · cada indicador tiene su ayuda con la fecha de corte', async ({ page }) => {
    for (const id of ['I1', 'I2', 'I3', 'I4']) {
      await page.getByRole('button', { name: new RegExp(`Cómo se calcula: ${id}`) }).focus()
      await expect(page.getByRole('tooltip').filter({ hasText: `${id} =` })).toContainText('Fecha de corte')
    }
  })
})

test.describe('HU-007 · Alertas R1–R4', () => {
  test.beforeEach(async ({ page }) => {
    await entrar(page)
    await dashboardDe(page, 1) // Biblioteca digital: dispara R1, R2, R3 y R4
  })

  test('CP-A1 · la lista agrupa las alertas por regla', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Alertas · 7' })).toBeVisible()
    for (const [filtro, cantidad] of [['Todas', 7], ['R1', 2], ['R2', 3], ['R3', 1], ['R4', 1]]) {
      await expect(page.getByRole('button', { name: `${filtro} (${cantidad})` })).toBeVisible()
    }
  })

  test('CP-A2 · el filtro deja solo las alertas de la regla elegida', async ({ page }) => {
    await page.getByRole('button', { name: /^R2 \(/ }).click()
    await expect(page.getByRole('button', { name: /Ver detalle y evidencia/ })).toHaveCount(3)
    await expect(page.getByRole('heading', { name: 'Tarea en curso sin ediciones' })).toHaveCount(3)
  })

  for (const [regla, titulo, tipo] of [
    ['R1', 'Tarea vencida', 'Fecha límite'],
    ['R2', 'Tarea en curso sin ediciones', 'Última edición'],
    ['R3', 'Repositorio sin commits', 'Último commit'],
    ['R4', 'Carpeta de Drive sin cambios', 'Último documento modificado'],
  ]) {
    test(`CP-A3 · ${regla} abre su detalle con explicación y evidencia`, async ({ page }) => {
      await page.getByRole('button', { name: new RegExp(`^${regla} \\(`) }).click()
      await page.getByRole('button', { name: /Ver detalle y evidencia/ }).first().click()

      await expect(page.getByRole('heading', { level: 1, name: titulo })).toBeVisible()
      await expect(page.getByRole('heading', { name: '¿Por qué se generó?' })).toBeVisible()
      await expect(page.getByText(`Regla ${regla}:`)).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Evidencia de origen' })).toBeVisible()
      await expect(page.getByText(`${tipo}:`)).toBeVisible()

      await page.getByRole('button', { name: 'Volver al Dashboard' }).click()
      await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
    })
  }
})
