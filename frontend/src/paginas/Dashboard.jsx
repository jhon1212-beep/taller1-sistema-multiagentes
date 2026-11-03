/**
 * TA-020 · Dashboard consolidado: indicadores, estado de fuentes y alertas.
 * HU-006 · Indicadores I1–I4 con la fórmula y la fecha de corte en una ayuda.
 * HU-007 · Lista de alertas R1–R4, filtrable por regla.
 */
import { useState } from 'react'
import { Aviso, Ayuda, Barra, Boton, Encabezado, Estadistica, Pill } from '../componentes/UI.jsx'
import { FECHA_CORTE, SUPERVISION_DEMO } from '../datos/demo_supervision.js'
import { INDICADORES, REGLAS, fechaHoraUtc, fechaUtc, formatoIndicador } from '../datos/indicadores.js'

/** Fuentes de evidencia del prototipo y el nombre de lo que aporta cada una. */
const FUENTES = [
  { id: 'github', nombre: 'GitHub', aporta: 'commits' },
  { id: 'notion', nombre: 'Notion', aporta: 'tareas' },
  { id: 'drive', nombre: 'Google Drive', aporta: 'documentos' },
]

/** Ayuda de un indicador: fórmula, cifras del proyecto y fecha de corte. */
function AyudaIndicador({ id, sup }) {
  const { tareas_total: total, tareas_listas: listas, ultima_actividad: ultima } = sup.detalle
  const cifras = {
    I1: `${listas} de ${total} tareas están en «Listo».`,
    I2: `${total - listas} de ${total} tareas están sin empezar o en curso.`,
    I3: `${sup.indicadores.I3} tareas no están «Listo» y ya pasó su fecha límite.`,
    I4: `Última actividad: ${fechaUtc(ultima)}.`,
  }[id]
  return (
    <Ayuda id={`ayuda-${id}`} etiqueta={`${id} · ${INDICADORES[id].etiqueta}`}>
      <b>{INDICADORES[id].formula}</b>
      <br />
      {cifras}
      <br />
      Fecha de corte: {fechaHoraUtc(FECHA_CORTE)}
    </Ayuda>
  )
}

function ListaAlertas({ alertas, onAlerta }) {
  const [filtro, setFiltro] = useState('todas')
  const reglas = Object.keys(REGLAS)
  const visibles = filtro === 'todas' ? alertas : alertas.filter(a => a.regla === filtro)

  return (
    <>
      <div className="filtros" role="group" aria-label="Filtrar alertas por regla">
        {['todas', ...reglas].map(r => {
          const cantidad = r === 'todas' ? alertas.length : alertas.filter(a => a.regla === r).length
          return (
            <button
              type="button"
              key={r}
              className="filtro"
              aria-pressed={filtro === r}
              onClick={() => setFiltro(r)}
            >
              {r === 'todas' ? 'Todas' : r} ({cantidad})
            </button>
          )
        })}
      </div>

      {visibles.length === 0 && <p className="muted">No hay alertas con este filtro.</p>}

      <ul className="lista-alertas" aria-label="Alertas del proyecto">
        {visibles.map(a => {
          const regla = REGLAS[a.regla]
          return (
            <li className="card alerta-item" key={a.id}>
              <div className="alerta-cab">
                <Pill>{a.regla}</Pill>
                <h3>{regla.titulo}</h3>
                <Pill>{regla.fuente}</Pill>
              </div>
              <p>
                <b>{a.evidencia.titulo}</b>
                {a.evidencia.responsable ? ` · ${a.evidencia.responsable}` : ''}
              </p>
              <Boton
                variante="secundario"
                aria-label={`Ver detalle y evidencia: ${a.regla} ${regla.titulo}, ${a.evidencia.titulo}`}
                onClick={() => onAlerta(a)}
              >
                Ver detalle y evidencia
              </Boton>
            </li>
          )
        })}
      </ul>
    </>
  )
}

export default function Dashboard({ proyecto, notionFallo, ultimaCorrida, onSimular, onAlerta }) {
  const [traza, setTraza] = useState(null)
  const sup = SUPERVISION_DEMO[proyecto.id]

  function simular() {
    const fecha = new Date().toLocaleString('es-PE')
    onSimular(fecha)
    const n = sup?.detalle.evidencias ?? { github: 0, notion: 0, drive: 0 }
    setTraza([
      'Supervisor: ejecución simulada iniciada',
      `GitHub: ${n.github} commits · OK`,
      `Notion: ${notionFallo ? '401/403 simulado · fallo controlado' : `${n.notion} tareas · OK`}`,
      `Drive: ${n.drive} documentos · OK`,
      'Analista: salida ilustrativa disponible',
      `Supervisor: consolidado ${notionFallo ? 'parcial' : 'completo'} registrado en Historial`,
    ])
  }

  const disponibles = FUENTES.filter(f => !(f.id === 'notion' && notionFallo)).length

  return (
    <>
      <Encabezado
        antetitulo="Dashboard / Resumen"
        titulo="Dashboard"
        descripcion={`Una vista consolidada de la evidencia y las alertas de ${proyecto.nombre}.`}
        accion={<Boton onClick={simular}>Simular supervisión</Boton>}
      />

      {sup ? (
        <Aviso>
          Fecha de corte: <b>{fechaHoraUtc(FECHA_CORTE)}</b>. Indicadores y alertas calculados por el
          motor de reglas (TA-019) sobre el dataset de demostración (TA-017).
        </Aviso>
      ) : (
        <Aviso>
          Este proyecto no tiene evidencia de demostración: los indicadores y las alertas se
          calcularán cuando se conecten sus fuentes.
        </Aviso>
      )}

      {sup && notionFallo && (
        <Aviso tipo="error">
          Notion no está disponible: los indicadores I1, I2 e I3 se calculan con la última lectura.
        </Aviso>
      )}

      <section aria-labelledby="dash-indicadores">
        <h2 id="dash-indicadores" className="seccion">Indicadores del proyecto</h2>
        {sup ? (
          <div className="grid cuatro">
            <Estadistica
              etiqueta={`${INDICADORES.I1.etiqueta} (I1)`}
              valor={formatoIndicador('I1', sup.indicadores.I1)}
              detalle={`${sup.detalle.tareas_listas} de ${sup.detalle.tareas_total} tareas · Notion`}
              ayuda={<AyudaIndicador id="I1" sup={sup} />}
            >
              <Barra porcentaje={sup.indicadores.I1} />
            </Estadistica>
            <Estadistica
              etiqueta={`${INDICADORES.I2.etiqueta} (I2)`}
              valor={formatoIndicador('I2', sup.indicadores.I2)}
              detalle="Sin empezar y en curso · Notion"
              ayuda={<AyudaIndicador id="I2" sup={sup} />}
            />
            <Estadistica
              etiqueta={`${INDICADORES.I3.etiqueta} (I3)`}
              valor={formatoIndicador('I3', sup.indicadores.I3)}
              detalle="Fecha límite anterior al corte · Notion"
              ayuda={<AyudaIndicador id="I3" sup={sup} />}
            />
            <Estadistica
              etiqueta={`${INDICADORES.I4.etiqueta} (I4)`}
              valor={formatoIndicador('I4', sup.indicadores.I4)}
              detalle={`Última actividad: ${fechaUtc(sup.detalle.ultima_actividad)}`}
              ayuda={<AyudaIndicador id="I4" sup={sup} />}
            />
          </div>
        ) : (
          <p className="muted">Sin datos que mostrar.</p>
        )}
      </section>

      <section aria-labelledby="dash-fuentes">
        <h2 id="dash-fuentes" className="seccion">
          Estado de las fuentes · {disponibles} de {FUENTES.length} disponibles
        </h2>
        <div className="grid tres">
          {FUENTES.map(f => {
            const caida = f.id === 'notion' && notionFallo
            const cantidad = sup?.detalle.evidencias[f.id] ?? 0
            return (
              <article className="card fuente-card" key={f.id}>
                <div className="fuente-cab">
                  <h3>{f.nombre}</h3>
                  <Pill tono={caida ? 'bad' : 'ok'}>{caida ? 'Integración fallida' : 'Disponible'}</Pill>
                </div>
                <p className="muted small">
                  {caida ? 'Sin datos: error de autorización simulado' : `${cantidad} ${f.aporta} leídos`}
                </p>
                <small className="muted">Última lectura: {ultimaCorrida}</small>
              </article>
            )
          })}
        </div>
      </section>

      <section aria-labelledby="dash-alerta">
        <h2 id="dash-alerta" className="seccion">
          Alertas{sup ? ` · ${sup.alertas.length}` : ''}
        </h2>
        {sup && sup.alertas.length > 0 ? (
          <ListaAlertas alertas={sup.alertas} onAlerta={onAlerta} />
        ) : (
          <article className="card">
            <p>No hay alertas para este proyecto en la fecha de corte.</p>
          </article>
        )}
      </section>

      <article className="card">
        <h3>Flujo de supervisión · 5 agentes</h3>
        <p>Supervisor → GitHub + Notion + Drive → Analista → resultado para el docente.</p>
        <p className="small muted">
          El prototipo representa el flujo; no ejecuta LangGraph, modelos ni llamadas externas.
        </p>
        {traza && (
          <div className="traza" role="status">
            {traza.map(linea => (
              <div key={linea}>{linea}</div>
            ))}
          </div>
        )}
      </article>
    </>
  )
}
