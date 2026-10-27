import { chromium } from '@playwright/test'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const AQUI = path.dirname(fileURLToPath(import.meta.url))
const DIR = path.resolve(AQUI, '../../docs/sprint2/evidencias/semana9/figma')
const b = await chromium.launch({ channel: 'msedge' })
for (const [svg, w, h, png] of [['TA-016_01_Dashboard.svg',1280,960,'P1_dashboard.png'],['TA-016_02_Detalle_de_alerta.svg',1280,760,'P2_detalle_alerta.png'],['TA-016_03_Historial.svg',1280,640,'P3_historial.png']]) {
  const p = await b.newPage({ viewport: { width: w, height: h } })
  await p.setContent(`<body style="margin:0">${readFileSync(path.join(DIR, svg), 'utf8')}</body>`)
  await p.screenshot({ path: path.join(DIR, png) })
}
await b.close()
