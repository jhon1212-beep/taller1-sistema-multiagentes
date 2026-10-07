/**
 * TA-005 · Componentes base de interfaz
 *
 * Primitivas reutilizables del sistema visual (EN-UI-001). Toda vista debe
 * construirse con estas piezas para que el estilo quede en un solo lugar.
 */

const clases = (...xs) => xs.filter(Boolean).join(' ')

/** Indicador de estado. tono: 'neutro' | 'ok' | 'warn' | 'bad' */
export function Pill({ tono = 'neutro', children }) {
  const mapa = { ok: 'pill-ok', warn: 'pill-warn', bad: 'pill-bad', neutro: '' }
  return <span className={clases('pill', mapa[tono])}>{children}</span>
}

/** Botón. variante: 'primario' | 'secundario' | 'peligro' */
export function Boton({ variante = 'primario', children, ...props }) {
  const mapa = { primario: '', secundario: 'btn-sec', peligro: 'btn-danger' }
  return (
    <button className={clases('btn', mapa[variante])} {...props}>
      {children}
    </button>
  )
}

/** Contenedor de contenido. */
export function Tarjeta({ titulo, children, ...props }) {
  return (
    <article className="card" {...props}>
      {titulo && <h3>{titulo}</h3>}
      {children}
    </article>
  )
}

/** Cifra destacada con etiqueta y detalle opcional. */
export function Estadistica({ etiqueta, valor, detalle, children }) {
  return (
    <div className="card stat">
      <small>{etiqueta}</small>
      <strong>{valor}</strong>
      {children}
      {detalle && <small>{detalle}</small>}
    </div>
  )
}

/** Barra de progreso. porcentaje: 0-100 */
export function Barra({ porcentaje }) {
  const valor = Math.max(0, Math.min(100, Number(porcentaje) || 0))
  return (
    <div
      className="barra"
      role="progressbar"
      aria-valuenow={valor}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <span style={{ width: `${valor}%` }} />
    </div>
  )
}

/** Tabla con encabezados y filas ya formateadas. */
export function Tabla({ columnas, filas, vacio = 'Sin datos para mostrar.' }) {
  if (!filas.length) return <p className="muted">{vacio}</p>
  return (
    <div className="tabla-wrap">
      <table>
        <thead>
          <tr>{columnas.map(c => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {filas.map((fila, i) => (
            <tr key={i}>{fila.map((celda, j) => <td key={j}>{celda}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Navegación por pestañas accesible. */
export function Tabs({ opciones, activa, onCambio }) {
  return (
    <div className="tabs" role="tablist">
      {Object.entries(opciones).map(([clave, etiqueta]) => (
        <button
          key={clave}
          role="tab"
          aria-selected={clave === activa}
          onClick={() => onCambio(clave)}
        >
          {etiqueta}
        </button>
      ))}
    </div>
  )
}

/** Mensaje informativo (aviso) o de error. */
export function Aviso({ tipo = 'info', children }) {
  return (
    <div className={tipo === 'error' ? 'error' : 'aviso'} role={tipo === 'error' ? 'alert' : undefined}>
      {children}
    </div>
  )
}

/** Campo de formulario con etiqueta asociada. */
export function Campo({ etiqueta, as = 'input', ayuda, ...props }) {
  const Etiqueta = as
  return (
    <label>
      {etiqueta}
      <Etiqueta {...props} />
      {ayuda && <span className="small muted">{ayuda}</span>}
    </label>
  )
}

/** Encabezado de página: antetítulo, título, descripción y acción. */
export function Encabezado({ antetitulo, titulo, descripcion, accion }) {
  return (
    <div className="head">
      <div>
        {antetitulo && <div className="eyebrow">{antetitulo}</div>}
        <h1>{titulo}</h1>
        {descripcion && <p className="muted">{descripcion}</p>}
      </div>
      {accion}
    </div>
  )
}
