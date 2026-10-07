/** TA-002 / TA-016 · Dashboard docente con evidencia y alertas. */
import { useState } from 'react'
import { Aviso, Barra, Boton, Encabezado, Estadistica, Pill } from '../componentes/UI.jsx'

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

  return (
    <>
      <Encabezado
        antetitulo="TA-002 / TA-016 · Dashboard docente"
        titulo="Dashboard"
        descripcion={`Una vista de la evidencia y las alertas de ${proyecto.nombre}.`}
        accion={<Boton onClick={simular}>Simular supervisión</Boton>}
      />

      <Aviso>
        Fecha de corte de ejemplo: 06/10/2026. Valores ilustrativos; no acreditan el motor I1–I4
        ni las reglas R1–R4.
      </Aviso>

      <div className="grid cuatro">
        <Estadistica etiqueta="Tareas completadas (ejemplo)" valor="40 %" detalle="8 de 20 tareas">
          <Barra porcentaje={40} />
        </Estadistica>
        <Estadistica etiqueta="Tareas pendientes" valor="12" detalle="Incluye tareas en progreso" />
        <Estadistica etiqueta="Commits mostrados" valor="20" detalle="Datos de demostración" />
        <Estadistica etiqueta="Documentos" valor="10" detalle="Datos de demostración" />
      </div>

      <div className="grid dos">
        <article className="card">
          <h3>Estado de las fuentes · Simulado</h3>
          <div className="fuente">
            GitHub <Pill tono="ok">Disponible</Pill>
          </div>
          <div className="fuente">
            Notion{' '}
            <Pill tono={notionFallo ? 'bad' : 'ok'}>
              {notionFallo ? 'Integración fallida' : 'Disponible'}
            </Pill>
          </div>
          <div className="fuente">
            Google Drive <Pill tono="ok">Disponible</Pill>
          </div>
          <p className="small muted" style={{ marginTop: 'var(--sp-4)' }}>
            Última simulación: {ultimaCorrida}
          </p>
        </article>

        <article className="card">
          <h3>Alerta de ejemplo</h3>
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
      </div>

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
