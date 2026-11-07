/**
 * TA-016 · Historial de supervisión.
 *
 * HU-009 · Con API activa compara los cortes guardados en PostgreSQL (TA-018)
 * con I1–I4, alertas por regla y la validación CP-17 del día, y ofrece un
 * reporte imprimible que el navegador guarda como PDF.
 * Sin API se mantiene el historial de ejecuciones simuladas de la sesión.
 */
import { useEffect, useState } from 'react'
import { API_ACTIVA, obtenerHistorial } from '../api.js'
import { Aviso, Boton, Encabezado, Pill, Tabla } from '../componentes/UI.jsx'
import { INDICADORES, REGLAS, formatoIndicador } from '../datos/indicadores.js'
import { diaCorte, mensajeError } from '../datos/supervision_api.js'

const IDS = ['I1', 'I2', 'I3', 'I4']

export default function Historial(props) {
  return API_ACTIVA ? <HistorialApi {...props} /> : <HistorialDemo {...props} />
}

function HistorialDemo({ corridas, onDashboard }) {
  return (
    <>
      <Encabezado
        antetitulo="Historial / Supervisión"
        titulo="Historial de supervisión"
        descripcion="Ejecuciones simuladas durante esta sesión; se reinician al recargar."
      />
      <article className="card">
        <Tabla
          columnas={['Fecha', 'Resultado', 'Tipo de evidencia']}
          filas={corridas.map(c => [c.fecha, c.estado, 'Simulación del prototipo'])}
          vacio="No hay ejecuciones en esta sesión."
        />
        <Boton variante="secundario" onClick={onDashboard} style={{ marginTop: 'var(--sp-4)' }}>
          Ir al Dashboard
        </Boton>
      </article>
    </>
  )
}

/** Diferencia entre dos valores de un indicador, con signo («+10 pts», «−2»). */
function diferencia(id, antes, despues) {
  if (antes == null || despues == null) return '—'
  const d = Math.round((despues - antes) * 100) / 100
  if (d === 0) return 'sin cambio'
  const signo = d > 0 ? '+' : '−'
  const valor = String(Math.abs(d)).replace('.', ',')
  return id === 'I1' || id === 'I2' ? `${signo}${valor} pts` : `${signo}${valor}`
}

const textoAlertas = c =>
  c.total_alertas === 0
    ? '0'
    : `${c.total_alertas} (${Object.entries(c.alertas_por_regla).map(([r, n]) => `${r}: ${n}`).join(', ')})`

const textoValidacion = v => (v ? `${v.resultado} · ${(v.duracion_ms / 1000).toFixed(1)} s` : 'Sin ejecutar')

function HistorialApi({ proyecto, onDashboard }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  const [comparar, setComparar] = useState({ a: null, b: null })

  useEffect(() => {
    if (!proyecto) return undefined
    const control = new AbortController()
    setDatos(null)
    setError('')
    obtenerHistorial(proyecto.id, { senal: control.signal })
      .then(r => {
        setDatos(r)
        const dias = r.cortes.map(c => c.fecha_corte)
        setComparar({ a: dias[Math.max(0, dias.length - 2)] ?? null, b: dias[dias.length - 1] ?? null })
      })
      .catch(e => { if (e.name !== 'AbortError') setError(mensajeError(e, 'No se pudo leer el historial')) })
    return () => control.abort()
  }, [proyecto])

  if (!proyecto) {
    return (
      <>
        <Encabezado antetitulo="Historial / Supervisión" titulo="Historial de supervisión" />
        <Aviso>Elige un proyecto en «Mis proyectos» para ver sus cortes.</Aviso>
      </>
    )
  }

  const cortes = datos?.cortes ?? []
  const corteA = cortes.find(c => c.fecha_corte === comparar.a)
  const corteB = cortes.find(c => c.fecha_corte === comparar.b)
  const emitido = new Date().toLocaleString('es-PE', { timeZone: 'America/Lima' })

  const selector = (clave, etiqueta) => (
    <label className="campo-corte">
      {etiqueta}
      <select value={comparar[clave] ?? ''} onChange={e => setComparar(c => ({ ...c, [clave]: e.target.value }))}>
        {cortes.map(c => <option key={c.fecha_corte} value={c.fecha_corte}>{diaCorte(c.fecha_corte)}</option>)}
      </select>
    </label>
  )

  return (
    <div className="reporte">
      <Encabezado
        antetitulo="Historial / Supervisión"
        titulo="Historial de supervisión"
        descripcion={`${proyecto.nombre} · ${proyecto.curso}. Cortes guardados en PostgreSQL, del más antiguo al más reciente.`}
        accion={
          <Boton className="no-imprimir" onClick={() => window.print()} disabled={!cortes.length}>
            Imprimir reporte
          </Boton>
        }
      />

      <p className="solo-imprimir small">
        Reporte emitido el {emitido} (hora de Lima). Cada corte corresponde al fin del día indicado.
      </p>

      {error && <Aviso tipo="error">{error}</Aviso>}
      {!datos && !error && <Aviso>Cargando los cortes del proyecto…</Aviso>}

      {datos && cortes.length === 0 && (
        <Aviso>
          Todavía no hay cortes guardados. Ejecuta la supervisión desde el Dashboard para crear el
          primero.
        </Aviso>
      )}

      {cortes.length > 0 && (
        <article className="card" aria-labelledby="hist-cortes">
          <div className="head">
            <h2 id="hist-cortes">Cortes del proyecto</h2>
            <Pill tono="ok">{datos.total_cortes} cortes</Pill>
          </div>
          <Tabla
            columnas={['Fecha de corte', 'I1', 'I2', 'I3', 'I4', 'Alertas', 'Validación CP-17']}
            filas={cortes.map(c => [
              diaCorte(c.fecha_corte),
              ...IDS.map(id => formatoIndicador(id, c.indicadores[id])),
              textoAlertas(c),
              textoValidacion(c.validacion),
            ])}
          />
          <p className="small muted">
            {IDS.map(id => `${id}: ${INDICADORES[id].etiqueta}`).join(' · ')}.{' '}
            {Object.entries(REGLAS).map(([r, x]) => `${r}: ${x.titulo}`).join(' · ')}.
          </p>
        </article>
      )}

      {cortes.length > 1 && corteA && corteB && (
        <article className="card" aria-labelledby="hist-comparar">
          <div className="head">
            <h2 id="hist-comparar">Comparación entre cortes</h2>
            <div className="acciones-corte no-imprimir">
              {selector('a', 'Corte anterior')}
              {selector('b', 'Corte posterior')}
            </div>
          </div>
          <Tabla
            columnas={['Indicador', diaCorte(corteA.fecha_corte), diaCorte(corteB.fecha_corte), 'Cambio']}
            filas={[
              ...IDS.map(id => [
                `${INDICADORES[id].etiqueta} (${id})`,
                formatoIndicador(id, corteA.indicadores[id]),
                formatoIndicador(id, corteB.indicadores[id]),
                diferencia(id, corteA.indicadores[id], corteB.indicadores[id]),
              ]),
              ['Alertas', textoAlertas(corteA), textoAlertas(corteB),
                diferencia('A', corteA.total_alertas, corteB.total_alertas)],
            ]}
          />
        </article>
      )}

      <Boton className="no-imprimir" variante="secundario" onClick={onDashboard} style={{ marginTop: 'var(--sp-4)' }}>
        Ir al Dashboard
      </Boton>
    </div>
  )
}
