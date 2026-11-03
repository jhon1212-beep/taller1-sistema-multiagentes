/**
 * TA-039 · Traduce un proyecto entre la forma de la API (HU-002) y la de las vistas.
 *
 * API:    { nombre, curso, fecha_inicio, fecha_fin, url_publica, elemento_verificar,
 *           integrantes: [{ nombre, correo }], fuentes: { github, notion, drive } }
 * Vistas: { nombre, curso, inicio, fin, url, selector, integrantes: 'A, B',
 *           github, notion, drive }
 */

export function deApi(p) {
  return {
    id: p.id,
    nombre: p.nombre,
    curso: p.curso,
    inicio: p.fecha_inicio,
    fin: p.fecha_fin,
    integrantes: p.integrantes.map(i => i.nombre).join(', '),
    github: p.fuentes.github,
    notion: p.fuentes.notion,
    drive: p.fuentes.drive,
    url: p.url_publica,
    selector: p.elemento_verificar,
    activo: p.activo,
  }
}

export function aApi(d) {
  return {
    nombre: d.nombre,
    curso: d.curso,
    fecha_inicio: d.inicio,
    fecha_fin: d.fin,
    url_publica: d.url,
    elemento_verificar: d.selector,
    integrantes: String(d.integrantes)
      .split(',')
      .map(n => n.trim())
      .filter(Boolean)
      .map(nombre => ({ nombre, correo: null })),
    fuentes: { github: d.github, notion: d.notion, drive: d.drive },
  }
}

/**
 * «2026-09-22T14:00:00Z» → «2026-09-22 14:00» (mismo formato que los datos de demostración).
 *
 * Siempre en UTC: la API devuelve la hora con el desfase de la zona del servidor
 * (por ejemplo «2026-10-12T04:00:00-05:00»), así que cortar el texto mostraría la
 * hora local como si fuera UTC. Se convierte primero con Date.
 */
export function fechaCorta16(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso ?? '')
  return d.toISOString().slice(0, 16).replace('T', ' ')
}
