/** TA-020 · Dashboard consolidado: indicadores, estado de fuentes y alerta. */
import { useState } from 'react'
import { Aviso, Barra, Boton, Encabezado, Estadistica, Pill } from '../componentes/UI.jsx'

/** Fuentes de evidencia del prototipo, con lo que aporta cada una. */
const FUENTES = [
  { id: 'github', nombre: 'GitHub', aporta: 'Commits', cantidad: 20 },
  { id: 'notion', nombre: 'Notion', aporta: 'Tareas', cantidad: 20 },
  { id: 'drive', nombre: 'Google Drive', aporta: 'Documentos', cantidad: 10 },
]

export default function Dashboard({ proyecto, notionFallo, ultimaCorrida, onSimular, onAlerta }) {
  const [traza, setTraza] = useState(null)

  function simular() {
    const fecha = new Date().toLocaleString('es-PE')
    onSimular(fecha)
    setTraza([
      'Supervisor: ejecución simulada iniciada',
      'GitHub: 20 commits · OK',
      `Notion: ${notionFallo ? '401/403 simulado · fallo controlado' : '20 tareas · OK'}`,
      'Drive: 10 documentos · OK',
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

      <Aviso>
        Fecha de corte de ejemplo: 06/10/2026. Valores ilustrativos; no acreditan el motor I1–I4
        ni las reglas R1–R4.
      </Aviso>

      <section aria-labelledby="dash-indicadores">
        <h2 id="dash-indicadores" className="seccion">Indicadores del proyecto</h2>
        <div className="grid cuatro">
          <Estadistica etiqueta="Tareas completadas" valor="40 %" detalle="8 de 20 tareas · Notion">
            <Barra porcentaje={40} />
          </Estadistica>
          <Estadistica etiqueta="Tareas pendientes" valor="12" detalle="Incluye tareas en progreso · Notion" />
          <Estadistica etiqueta="Commits registrados" valor="20" detalle="Datos de demostración · GitHub" />
          <Estadistica etiqueta="Documentos" valor="10" detalle="Datos de demostración · Google Drive" />
        </div>
      </section>

      <section aria-labelledby="dash-fuentes">
        <h2 id="dash-fuentes" className="seccion">
          Estado de las fuentes · {disponibles} de {FUENTES.length} disponibles
        </h2>
        <div className="grid tres">
          {FUENTES.map(f => {
            const caida = f.id === 'notion' && notionFallo
            return (
              <article className="card fuente-card" key={f.id}>
                <div className="fuente-cab">
                  <h3>{f.nombre}</h3>
                  <Pill tono={caida ? 'bad' : 'ok'}>{caida ? 'Integración fallida' : 'Disponible'}</Pill>
                </div>
                <p className="muted small">
                  {caida ? 'Sin datos: error de autorización simulado' : `${f.cantidad} ${f.aporta.toLowerCase()} leídos`}
                </p>
                <small className="muted">Última lectura: {ultimaCorrida}</small>
              </article>
            )
          })}
        </div>
      </section>

      <section aria-labelledby="dash-alerta">
        <h2 id="dash-alerta" className="seccion">Alertas</h2>
        <article className="card">
          <Pill tono="warn">Requiere revisión docente</Pill>
          <h3 style={{ marginTop: 'var(--sp-4)' }}>Entregable con fecha vencida</h3>
          <p>
            La tarea «Documentar pruebas» continúa pendiente después de la fecha de entrega del
            ejemplo.
          </p>
          <Boton variante="secundario" onClick={onAlerta}>
            Ver detalle y evidencia
          </Boton>
        </article>
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
