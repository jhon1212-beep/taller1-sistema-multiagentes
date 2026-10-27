// TA-016 · Genera los 3 frames (Dashboard, Detalle de alerta, Historial) como SVG
// con los tokens de EN-UI-001, para pegarlos en Figma.
import { writeFileSync } from 'node:fs'

const C = { brand: '#1f4e78', brand2: '#2e75b6', soft: '#eaf2fb', bg: '#f4f6fa', panel: '#ffffff', ink: '#1b2333', muted: '#6b7488', line: '#e2e6ee', ok: '#1f9d55', warn: '#e0a100', bad: '#d64545', okbg: '#e6f6ec', warnbg: '#fff6da', badbg: '#fde9e9' }
const F = 'Inter, Segoe UI, sans-serif'
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;')

const t = (x, y, s, { size = 14, w = 400, fill = C.ink, anchor = 'start' } = {}) =>
  `<text x="${x}" y="${y}" font-family="${F}" font-size="${size}" font-weight="${w}" fill="${fill}" text-anchor="${anchor}">${esc(s)}</text>`
const r = (x, y, w, h, { fill = C.panel, stroke = C.line, rx = 12 } = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}"${stroke ? ` stroke="${stroke}"` : ''}/>`
const pill = (x, y, s, tono) => {
  const m = { ok: [C.okbg, C.ok], warn: [C.warnbg, C.warn], bad: [C.badbg, C.bad], neutro: [C.soft, C.brand] }[tono]
  const w = s.length * 6.8 + 24
  return r(x, y, w, 24, { fill: m[0], stroke: null, rx: 12 }) + t(x + 12, y + 16, s, { size: 12, w: 600, fill: m[1] })
}
const btn = (x, y, w, s, sec) =>
  r(x, y, w, 44, { fill: sec ? C.panel : C.brand2, stroke: sec ? C.line : null, rx: 8 }) +
  t(x + w / 2, y + 27, s, { size: 14, w: 600, fill: sec ? C.brand : '#fff', anchor: 'middle' })

function shell(activo, ante, titulo, desc, accion, cuerpo, H) {
  const nav = ['Mis proyectos', 'Dashboard', 'Historial', 'Sistema visual'].map((n, i) => {
    const y = 124 + i * 54
    const on = n === activo
    return (on ? r(16, y, 206, 46, { fill: '#fff', stroke: null, rx: 8 }) : '') +
      t(28, y + 28, n, { size: 14, w: on ? 700 : 400, fill: on ? C.brand : '#fff' })
  }).join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="${H}" viewBox="0 0 1280 ${H}">
<rect width="1280" height="${H}" fill="${C.bg}"/>
<rect width="1280" height="36" fill="#fff3cd"/>${t(640, 23, 'Prototipo navegable · Datos simulados. Acceso exclusivo del docente.', { size: 12, w: 600, anchor: 'middle', fill: '#664d03' })}
<rect y="36" width="238" height="${H - 36}" fill="${C.brand}"/>
${t(34, 86, '◈ AgenteSeguimiento', { size: 15, w: 700, fill: '#fff' })}${t(16, 106, 'Supervisión académica', { size: 11.5, fill: '#fff' })}
${nav}
${t(16, H - 90, 'Cuenta docente', { size: 14, w: 700, fill: '#fff' })}${t(16, H - 70, 'docente1@demo.test', { size: 11.5, fill: '#fff' })}${r(16, H - 58, 117, 46, { rx: 8, stroke: null })}${t(74, H - 30, 'Cerrar sesión', { size: 14, w: 600, fill: C.brand, anchor: 'middle' })}
${t(270, 82, ante.toUpperCase(), { size: 12, w: 700, fill: C.brand2 })}${t(270, 120, titulo, { size: 28, w: 700 })}${t(270, 150, desc, { size: 14, fill: C.muted })}
${accion}
${cuerpo}
${t(270, H - 24, 'Maqueta con datos de demostración · Las acciones representan el flujo propuesto.', { size: 11.5, fill: C.muted })}
</svg>`
}

const aviso = (y, s) => r(270, y, 978, 54, { fill: C.soft, stroke: null, rx: 10 }) + t(286, y + 32, s, { size: 14 })
const kpi = (x, y, et, val, det, barra) =>
  r(x, y, 232, 150) + t(x + 24, y + 36, et, { size: 12.5, fill: C.muted }) + t(x + 24, y + 74, val, { size: 26, w: 700, fill: C.brand }) +
  (barra != null
    ? `<rect x="${x + 24}" y="${y + 90}" width="184" height="8" rx="4" fill="${C.line}"/><rect x="${x + 24}" y="${y + 90}" width="${(184 * barra) / 100}" height="8" rx="4" fill="${C.brand2}"/>`
    : '') +
  t(x + 24, y + (barra != null ? 126 : 106), det, { size: 12.5, fill: C.muted })

// 01 · Dashboard
let d = aviso(184, 'Fecha de corte de ejemplo: 06/10/2026. Valores ilustrativos; no acreditan el motor I1–I4 ni las reglas R1–R4.')
d += t(270, 288, 'Indicadores del proyecto', { size: 15, w: 700 })
d += kpi(270, 306, 'Tareas completadas', '40 %', '8 de 20 tareas · Notion', 40)
d += kpi(519, 306, 'Tareas pendientes', '12', 'Incluye en progreso · Notion')
d += kpi(768, 306, 'Commits registrados', '20', 'Datos de demostración · GitHub')
d += kpi(1017, 306, 'Documentos', '10', 'Datos de demostración · Drive')
d += t(270, 508, 'Estado de las fuentes · 3 de 3 disponibles', { size: 15, w: 700 })
;[['GitHub', '20 commits leídos'], ['Notion', '20 tareas leídas'], ['Google Drive', '10 documentos leídos']].forEach(([n, s], i) => {
  const x = 270 + i * 332
  d += r(x, 526, 314, 130) + t(x + 24, 566, n, { size: 15, w: 700 }) + pill(x + 314 - 24 - 91, 548, 'Disponible', 'ok') +
    t(x + 24, 602, s, { size: 14, fill: C.muted }) + t(x + 24, 634, 'Última lectura: 06/10/2026, 10:30', { size: 12, fill: C.muted })
})
d += t(270, 700, 'Alertas', { size: 15, w: 700 }) + r(270, 716, 978, 190) + pill(294, 736, 'Requiere revisión docente', 'warn') +
  t(294, 792, 'Entregable con fecha vencida', { size: 15, w: 700 }) +
  t(294, 820, 'La tarea «Documentar pruebas» continúa pendiente después de la fecha de entrega del ejemplo.', { size: 14 }) +
  btn(294, 840, 200, 'Ver detalle y evidencia', true)
writeFileSync('TA-016_01_Dashboard.svg', shell('Dashboard', 'Dashboard / Resumen', 'Dashboard', 'Una vista consolidada de la evidencia y las alertas de Seguimiento académico.', btn(1060, 99, 188, 'Simular supervisión'), d, 960))

// 02 · Detalle de alerta
let a = r(270, 184, 978, 420) + pill(294, 208, 'Ejemplo ilustrativo', 'warn') + t(294, 264, 'Causa y evidencia', { size: 15, w: 700 })
;[['Proyecto', 'Seguimiento académico'], ['Tarea', 'Documentar pruebas'], ['Responsable del equipo', 'Ana Torres'], ['Fecha límite de ejemplo', '05/10/2026'], ['Fecha de corte', '06/10/2026'], ['Estado de ejemplo', 'Pendiente']].forEach(([k, v], i) => {
  const y = 300 + i * 38
  a += t(294, y, k + ':', { size: 14, w: 700 }) + t(294 + k.length * 7.6 + 14, y, v, { size: 14 }) +
    `<line x1="294" x2="1224" y1="${y + 14}" y2="${y + 14}" stroke="${C.line}"/>`
})
a += t(294, 544, 'Alerta independiente del conjunto de 20 tareas: escenario ilustrativo para validar el diseño de esta pantalla.', { size: 13, fill: C.muted })
a += btn(294, 556, 230, 'Marcar revisada en demo') + btn(540, 556, 200, 'Volver al Dashboard', true)
writeFileSync('TA-016_02_Detalle_de_alerta.svg', shell('Dashboard', 'Dashboard / Detalle de alerta', 'Entregable con fecha vencida', 'Alerta de ejemplo · Requiere revisión docente.', '', a, 760))

// 03 · Historial
let h = r(270, 184, 978, 330) + r(270, 184, 978, 48, { fill: C.soft, stroke: null, rx: 12 })
;[['Fecha', 294], ['Resultado', 560], ['Tipo de evidencia', 900]].forEach(([c, x]) => { h += t(x, 214, c, { size: 12.5, w: 700, fill: C.brand }) })
;[['27/10/2026, 10:30', 'Completado (simulado)', 'ok'], ['27/10/2026, 09:55', 'Parcial: Notion falló', 'bad'], ['26/10/2026, 18:12', 'Completado (simulado)', 'ok'], ['26/10/2026, 16:40', 'Completado (simulado)', 'ok']].forEach(([f, e, tono], i) => {
  const y = 232 + i * 56
  h += t(294, y + 34, f, { size: 14 }) + pill(560, y + 16, e, tono) + t(900, y + 34, 'Simulación del prototipo', { size: 14, fill: C.muted }) +
    `<line x1="270" x2="1248" y1="${y + 56}" y2="${y + 56}" stroke="${C.line}"/>`
})
h += btn(294, 456, 170, 'Ir al Dashboard', true)
writeFileSync('TA-016_03_Historial.svg', shell('Historial', 'Historial / Supervisión', 'Historial de supervisión', 'Ejecuciones simuladas durante esta sesión; se reinician al recargar.', '', h, 640))
console.log('svg ok')
