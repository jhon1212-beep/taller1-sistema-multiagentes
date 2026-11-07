/**
 * TA-040 · Dashboard conectado a la API real de supervisión (TA-022).
 *
 * HU-006 · I1–I4 del corte elegido, con su fórmula y la fecha de corte.
 * HU-007 · Alertas R1–R4 del mismo corte, cada una con su evidencia de origen.
 * TA-020 · Estado de GitHub, Notion y Google Drive y espacio de validación (CP-17).
 *
 * «Ejecutar supervisión» llama a POST /proyectos/{id}/consolidacion: el backend
 * corre el grafo de agentes, guarda el corte en PostgreSQL y devuelve el
 * consolidado. Después se vuelven a leer indicadores, alertas e historial.
 */
import { useCallback, useEffect, useState } from 'react'
import {
  ejecutarConsolidacion, obtenerAlertas, obtenerHistorial, obtenerIndicadores, obtenerValidaciones,
} from '../api.js'
import { Aviso, Ayuda, Barra, Boton, Encabezado, Estadistica, Pill } from '../componentes/UI.jsx'
import ListaAlertas from '../componentes/ListaAlertas.jsx'
import { INDICADORES, fechaHoraUtc, formatoIndicador } from '../datos/indicadores.js'
import {
  ESTADO_FUENTE, alertaDeApi, corteFinDeDia, diaCorte, hoyEnLima, mensajeError, textoCorte,
} from '../datos/supervision_api.js'

const FUENTES = [
  { id: 'github', nombre: 'GitHub', aporta: 'commits' },
  { id: 'notion', nombre: 'Notion', aporta: 'tareas' },
  { id: 'drive', nombre: 'Google Drive', aporta: 'documentos' },
]

function AyudaIndicador({ id, valor, dia }) {
  return (
    <Ayuda id={`ayuda-${id}`} etiqueta={`${id} · ${INDICADORES[id].etiqueta}`}>
      <b>{INDICADORES[id].formula}</b>
      <br />
      Valor guardado en el corte: {formatoIndicador(id, valor)}.
      <br />
      Fecha de corte: {textoCorte(dia)}
    </Ayuda>
  )
}

/** Líneas de la traza a partir de la respuesta real de POST /consolidacion. */
function trazaDe(r) {
  const fuente = id => {
    const f = r.fuentes?.[id] ?? {}
    const nombre = FUENTES.find(x => x.id === id).nombre
    return f.estado === 'ok'
      ? `${nombre}: ${f.evidencias} evidencias · OK`
      : `${nombre}: ${f.error ?? 'fallo'} · fallo controlado`
  }
  const origenes = [...new Set((r.alertas ?? []).map(a => a.origen_explicacion))].join(', ') || '—'
  return [
    `Supervisor: corte ${r.fecha_corte} iniciado`,
    fuente('github'),
    fuente('notion'),
    fuente('drive'),
    `Motor de reglas: I1 ${formatoIndicador('I1', r.indicadores.I1)} · I2 ${formatoIndicador('I2', r.indicadores.I2)} · I3 ${r.indicadores.I3} · I4 ${formatoIndicador('I4', r.indicadores.I4)}`,
    `Explicación: ${r.alertas?.length ?? 0} alertas (origen: ${origenes})`,
    `PostgreSQL: ${r.guardado?.evidencias ?? 0} evidencias y ${r.guardado?.alertas ?? 0} alertas guardadas`,
    `Duración: grafo ${r.duracion_grafo_ms} ms · servicio ${r.duracion_servicio_ms} ms`,
  ]
}

export default function DashboardApi({ proyecto, onAlerta, onValidacion, onHistorial }) {
  const [cortes, setCortes] = useState([])
  const [dia, setDia] = useState(null) // null = el corte más reciente
  const [datos, setDatos] = useState(null) // { indicadores, alertas } del corte mostrado
  const [estado, setEstado] = useState('cargando') // cargando | listo | sin_cortes | error
  const [error, setError] = useState('')
  const [nuevoCorte, setNuevoCorte] = useState(hoyEnLima)
  const [ejecutando, setEjecutando] = useState(false)
  const [ejecucion, setEjecucion] = useState(null) // última respuesta de /consolidacion
  const [validacion, setValidacion] = useState(undefined)

  const cargar = useCallback(async (diaPedido, senal) => {
    setEstado('cargando')
    setError('')
    try {
      const [historial, indicadores, alertas] = await Promise.all([
        obtenerHistorial(proyecto.id, { senal }),
        obtenerIndicadores(proyecto.id, diaPedido, { senal }),
        obtenerAlertas(proyecto.id, diaPedido, { senal }),
      ])
      setCortes(historial.cortes.map(c => c.fecha_corte).reverse())
      setDatos({
        indicadores,
        alertas: alertas.alertas.map(a => alertaDeApi(a, alertas.fecha_corte, proyecto)),
      })
      setEstado('listo')
    } catch (e) {
      if (e.name === 'AbortError') return
      if (e.estado === 404) {
        setDatos(null)
        setEstado('sin_cortes')
        return
      }
      setError(mensajeError(e, 'No se pudo leer la supervisión'))
      setEstado('error')
    }
  }, [proyecto])

  useEffect(() => {
    const control = new AbortController()
    cargar(dia ?? undefined, control.signal)
    return () => control.abort()
  }, [cargar, dia])

  // Espacio de validación funcional: último CP-17 registrado (HU-008).
  useEffect(() => {
    const control = new AbortController()
    setValidacion(undefined)
    obtenerValidaciones(proyecto.id, { senal: control.signal })
      .then(r => setValidacion(r.items[0] ?? null))
      .catch(e => { if (e.name !== 'AbortError') setValidacion(null) })
    return () => control.abort()
  }, [proyecto.id])

  // Al cambiar de proyecto se vuelve al corte más reciente.
  useEffect(() => { setDia(null); setEjecucion(null) }, [proyecto.id])

  async function ejecutar() {
    setEjecutando(true)
    setError('')
    try {
      const r = await ejecutarConsolidacion(proyecto.id, corteFinDeDia(nuevoCorte))
      setEjecucion(r)
      const diaNuevo = r.fecha_corte.slice(0, 10)
      if (dia === diaNuevo) cargar(diaNuevo)
      else setDia(diaNuevo)
    } catch (e) {
      setError(mensajeError(e, 'No se pudo ejecutar la supervisión'))
    } finally {
      setEjecutando(false)
    }
  }

  const ind = datos?.indicadores
  const diaMostrado = ind?.fecha_corte
  const ejecucionDelCorte = ejecucion && ejecucion.fecha_corte.slice(0, 10) === diaMostrado ? ejecucion : null
  const estados = ind?.estado_fuentes ?? {}
  const disponibles = FUENTES.filter(f => estados[f.id] === 'ok').length

  const accion = (
    <div className="acciones-corte">
      <label className="campo-corte">
        Fecha de corte
        <input
          type="date"
          value={nuevoCorte}
          max={hoyEnLima()}
          onChange={e => setNuevoCorte(e.target.value)}
          disabled={ejecutando}
        />
      </label>
      <Boton onClick={ejecutar} disabled={ejecutando || !proyecto.activo || !nuevoCorte}>
        {ejecutando ? 'Ejecutando agentes…' : 'Ejecutar supervisión'}
      </Boton>
    </div>
  )

  return (
    <>
      <Encabezado
        antetitulo="Dashboard / Resumen"
        titulo="Dashboard"
        descripcion={`Una vista consolidada de la evidencia y las alertas de ${proyecto.nombre}.`}
        accion={accion}
      />

      {!proyecto.activo && (
        <Aviso>Este proyecto está desactivado: se pueden consultar sus cortes, pero no ejecutar nuevos.</Aviso>
      )}

      {ejecutando && (
        <Aviso>
          Los agentes están leyendo GitHub, Notion y Google Drive. Si el servidor estaba en reposo,
          la primera respuesta puede tardar hasta un minuto.
        </Aviso>
      )}

      {error && <Aviso tipo="error">{error}</Aviso>}

      {estado === 'cargando' && <Aviso>Cargando el último corte del proyecto…</Aviso>}

      {estado === 'sin_cortes' && (
        <Aviso>
          Este proyecto todavía no tiene cortes guardados. Elige la fecha de corte y pulsa
          «Ejecutar supervisión» para que los agentes calculen sus indicadores y alertas.
        </Aviso>
      )}

      {estado === 'listo' && (
        <div className="aviso barra-corte">
          <span>
            Fecha de corte: <b>{textoCorte(diaMostrado)}</b>. Indicadores y alertas guardados en
            PostgreSQL por el motor de reglas.
          </span>
          {cortes.length > 1 && (
            <label className="campo-corte">
              Ver corte
              <select value={diaMostrado} onChange={e => setDia(e.target.value)}>
                {cortes.map(c => (
                  <option key={c} value={c}>{diaCorte(c)}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      )}

      {estado === 'listo' && FUENTES.some(f => estados[f.id] === 'fallo') && (
        <Aviso tipo="error">
          Alguna fuente falló en la última lectura: los indicadores se calcularon con la evidencia
          disponible y la fuente caída queda marcada abajo.
        </Aviso>
      )}

      <section aria-labelledby="dash-indicadores">
        <h2 id="dash-indicadores" className="seccion">Indicadores del proyecto</h2>
        {ind ? (
          <div className="grid cuatro">
            <Estadistica
              etiqueta={`${INDICADORES.I1.etiqueta} (I1)`}
              valor={formatoIndicador('I1', ind.indicadores.I1)}
              detalle="Tareas en «Listo» · Notion"
              ayuda={<AyudaIndicador id="I1" valor={ind.indicadores.I1} dia={diaMostrado} />}
            >
              <Barra porcentaje={ind.indicadores.I1 ?? 0} />
            </Estadistica>
            <Estadistica
              etiqueta={`${INDICADORES.I2.etiqueta} (I2)`}
              valor={formatoIndicador('I2', ind.indicadores.I2)}
              detalle="Sin empezar y en curso · Notion"
              ayuda={<AyudaIndicador id="I2" valor={ind.indicadores.I2} dia={diaMostrado} />}
            />
            <Estadistica
              etiqueta={`${INDICADORES.I3.etiqueta} (I3)`}
              valor={formatoIndicador('I3', ind.indicadores.I3)}
              detalle="Fecha límite anterior al corte · Notion"
              ayuda={<AyudaIndicador id="I3" valor={ind.indicadores.I3} dia={diaMostrado} />}
            />
            <Estadistica
              etiqueta={`${INDICADORES.I4.etiqueta} (I4)`}
              valor={formatoIndicador('I4', ind.indicadores.I4)}
              detalle="Desde la última evidencia · 3 fuentes"
              ayuda={<AyudaIndicador id="I4" valor={ind.indicadores.I4} dia={diaMostrado} />}
            />
          </div>
        ) : (
          <p className="muted">Sin datos que mostrar.</p>
        )}
      </section>

      <section aria-labelledby="dash-fuentes">
        <h2 id="dash-fuentes" className="seccion">
          Estado de las fuentes{ind ? ` · ${disponibles} de ${FUENTES.length} disponibles` : ''}
        </h2>
        <div className="grid tres">
          {FUENTES.map(f => {
            const e = ESTADO_FUENTE[estados[f.id]] ?? ESTADO_FUENTE.pendiente
            const leida = ejecucionDelCorte?.fuentes?.[f.id]
            return (
              <article className="card fuente-card" key={f.id}>
                <div className="fuente-cab">
                  <h3>{f.nombre}</h3>
                  <Pill tono={e.tono}>{e.texto}</Pill>
                </div>
                <p className="muted small">
                  {leida
                    ? leida.estado === 'ok'
                      ? `${leida.evidencias} ${f.aporta} leídos en esta ejecución`
                      : leida.error
                    : 'Estado registrado en la última sincronización.'}
                </p>
                <small className="muted">Referencia: {proyecto[f.id] || '—'}</small>
              </article>
            )
          })}
        </div>
      </section>

      <section aria-labelledby="dash-alerta">
        <h2 id="dash-alerta" className="seccion">
          Alertas{datos ? ` · ${datos.alertas.length}` : ''}
        </h2>
        {datos && datos.alertas.length > 0 ? (
          <ListaAlertas alertas={datos.alertas} onAlerta={onAlerta} />
        ) : (
          <article className="card">
            <p>{datos ? 'No hay alertas para este proyecto en la fecha de corte.' : 'Sin corte que mostrar.'}</p>
          </article>
        )}
      </section>

      <div className="grid dos" style={{ alignItems: 'start' }}>
        <article className="card">
          <h3>Validación funcional · CP-17</h3>
          {validacion === undefined && <p className="muted">Consultando…</p>}
          {validacion === null && <p className="muted">Todavía no hay validaciones de la URL pública.</p>}
          {validacion && (
            <p>
              <Pill tono={validacion.resultado === 'PASS' ? 'ok' : 'bad'}>{validacion.resultado}</Pill>{' '}
              {fechaHoraUtc(validacion.ejecutada_en)} · {(validacion.duracion_ms / 1000).toFixed(1)} s
            </p>
          )}
          <Boton variante="secundario" onClick={onValidacion}>Ver validación</Boton>
        </article>

        <article className="card">
          <h3>Flujo de supervisión · 5 agentes</h3>
          <p>Supervisor → GitHub + Notion + Drive → Analista → resultado para el docente.</p>
          {ejecucion ? (
            <div className="traza" role="status">
              {trazaDe(ejecucion).map(linea => <div key={linea}>{linea}</div>)}
            </div>
          ) : (
            <p className="small muted">
              Pulsa «Ejecutar supervisión» para ver aquí la traza real de la última ejecución.
            </p>
          )}
          <Boton variante="secundario" onClick={onHistorial} style={{ marginTop: 'var(--sp-4)' }}>
            Ver historial de cortes
          </Boton>
        </article>
      </div>
    </>
  )
}
