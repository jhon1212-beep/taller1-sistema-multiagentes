/**
 * TA-008 · Pruebas E2E del inicio de sesión del docente (HU-001)
 *
 * Cubren los criterios de aceptación de la historia:
 *   - El docente entra con credenciales válidas y llega a Mis proyectos.
 *   - Las credenciales inválidas se rechazan con un mensaje claro.
 *   - Las rutas privadas no se pueden abrir sin sesión.
 *   - Cerrar sesión devuelve el acceso al estado bloqueado.
 *
 * Los selectores se basan en roles accesibles (getByRole / getByLabel) en vez
 * de clases CSS: si cambia el estilo las pruebas siguen valiendo, y si se
 * rompe la accesibilidad las pruebas se enteran.
 */
import { expect, test } from '@playwright/test'

const CORREO = 'docente1@demo.test'
const CLAVE = 'DemoDocente2026!'

/** Rellena el formulario y envía. */
async function iniciarSesion(page, correo = CORREO, clave = CLAVE) {
  if (correo) await page.getByLabel('Correo del docente').fill(correo)
  if (clave) await page.getByLabel('Contraseña', { exact: true }).fill(clave)
  await page.getByRole('button', { name: 'Ingresar' }).click()
}

test.describe('TA-008 · Inicio de sesión del docente', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('CP-L1 · muestra el formulario de inicio de sesión al entrar sin sesión', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
    await expect(page.getByLabel('Correo del docente')).toBeVisible()
    await expect(page.getByLabel('Contraseña', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Ingresar' })).toBeVisible()
    // Sin sesión no debe existir la navegación privada.
    await expect(page.getByRole('button', { name: 'Mis proyectos' })).toHaveCount(0)
  })

  test('CP-L2 · con credenciales válidas entra y muestra la cuenta activa', async ({ page }) => {
    await iniciarSesion(page)

    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible()
    await expect(page).toHaveURL(/#proyectos$/)
    // El correo de la sesión queda visible en la barra lateral.
    await expect(page.getByText(CORREO)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Cerrar sesión' })).toBeVisible()
  })

  test('CP-L3 · rechaza una contraseña incorrecta y no deja entrar', async ({ page }) => {
    await iniciarSesion(page, CORREO, 'clave-que-no-es')

    await expect(page.getByRole('alert')).toContainText('Correo o contraseña incorrectos')
    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toHaveCount(0)
  })

  test('CP-L4 · rechaza un correo no registrado', async ({ page }) => {
    await iniciarSesion(page, 'ajeno@otrodominio.test', CLAVE)

    await expect(page.getByRole('alert')).toContainText('Correo o contraseña incorrectos')
    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  })

  test('CP-L5 · pide completar los campos cuando se envía vacío', async ({ page }) => {
    await page.getByRole('button', { name: 'Ingresar' }).click()

    await expect(page.getByRole('alert')).toContainText('Completa el correo y la contraseña')
    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
  })

  test('CP-L6 · una ruta privada sin sesión devuelve al login con aviso', async ({ page }) => {
    await page.goto('/#dashboard')

    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()
    await expect(page.getByRole('alert')).toContainText('Debes iniciar sesión')
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toHaveCount(0)
  })

  test('CP-L7 · al cerrar sesión se vuelve al login y la ruta privada queda bloqueada', async ({ page }) => {
    await iniciarSesion(page)
    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible()

    await page.getByRole('button', { name: 'Cerrar sesión' }).click()
    await expect(page.getByRole('heading', { name: 'Iniciar sesión' })).toBeVisible()

    // Reintentar la ruta privada tras salir debe seguir bloqueado.
    await page.goto('/#dashboard')
    await expect(page.getByRole('alert')).toContainText('Debes iniciar sesión')
  })

  test('CP-L8 · la contraseña no se muestra en pantalla mientras se escribe', async ({ page }) => {
    const campoClave = page.getByLabel('Contraseña', { exact: true })
    await campoClave.fill(CLAVE)
    await expect(campoClave).toHaveAttribute('type', 'password')
  })
})
