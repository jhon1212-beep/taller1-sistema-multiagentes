/**
 * TA-047 · Validación E2E con parámetros (CP-17).
 *
 * Abre la URL pública del proyecto y comprueba que el elemento indicado
 * aparezca. Lo ejecuta el workflow .github/workflows/e2e.yml, pero también
 * se puede correr a mano con las mismas variables.
 *
 * Parámetros (variables de entorno, para que nunca pasen por el shell):
 *   URL_PUBLICA          URL a abrir (obligatoria)
 *   ELEMENTO_VERIFICAR   selector CSS que debe estar visible (obligatorio)
 *   PROYECTO_ID          id del proyecto, solo se copia al resultado
 *   SALIDA               carpeta de artefactos (por defecto ./resultados)
 *   E2E_CANAL            canal del navegador, p. ej. msedge (opcional)
 *
 * Artefactos: resultados/resultado.json siempre; resultados/captura.png solo en FAIL.
 * Código de salida: 0 = PASS, 1 = FAIL (así el run de Actions queda en failure).
 */
import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

const { URL_PUBLICA, ELEMENTO_VERIFICAR, PROYECTO_ID, E2E_CANAL } = process.env
const SALIDA = path.resolve(process.env.SALIDA ?? 'resultados')
const TIEMPO_MAX_MS = 10_000

if (!URL_PUBLICA?.trim() || !ELEMENTO_VERIFICAR?.trim()) {
  console.error('Faltan URL_PUBLICA y/o ELEMENTO_VERIFICAR.')
  process.exit(2)
}
try {
  const { protocol } = new URL(URL_PUBLICA)
  if (!['http:', 'https:'].includes(protocol)) throw new Error('protocolo')
} catch {
  console.error('URL_PUBLICA debe ser una URL http(s) válida.')
  process.exit(2)
}

await mkdir(SALIDA, { recursive: true })
const inicio = Date.now()
const navegador = await chromium.launch(E2E_CANAL ? { channel: E2E_CANAL } : {})
const pagina = await navegador.newPage({ viewport: { width: 1280, height: 800 } })

let resultado = 'PASS'
let detalle = ''
try {
  await pagina.goto(URL_PUBLICA, { timeout: TIEMPO_MAX_MS, waitUntil: 'domcontentloaded' })
  await pagina.locator(ELEMENTO_VERIFICAR).first().waitFor({ state: 'visible', timeout: TIEMPO_MAX_MS })
  detalle = `Elemento «${ELEMENTO_VERIFICAR}» visible en ${URL_PUBLICA}`
} catch (error) {
  resultado = 'FAIL'
  detalle = String(error.message ?? error).split('\n')[0]
  await pagina.screenshot({ path: path.join(SALIDA, 'captura.png'), fullPage: true }).catch(() => {})
}
await navegador.close()

const salida = {
  proyecto_id: PROYECTO_ID ? Number(PROYECTO_ID) : null,
  url_publica: URL_PUBLICA,
  elemento_verificar: ELEMENTO_VERIFICAR,
  resultado,
  duracion_ms: Date.now() - inicio,
  ejecutada_en: new Date().toISOString(),
  detalle,
}
await writeFile(path.join(SALIDA, 'resultado.json'), JSON.stringify(salida, null, 2))
console.log(JSON.stringify(salida))
process.exit(resultado === 'PASS' ? 0 : 1)
