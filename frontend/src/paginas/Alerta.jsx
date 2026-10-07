/** TA-016 · Detalle de una alerta con su causa y evidencia. */
import { useState } from 'react'
import { Boton, Encabezado, Pill } from '../componentes/UI.jsx'

export default function Alerta({ proyecto, onVolver }) {
  const [revisada, setRevisada] = useState(false)

  const datos = [
    ['Proyecto', proyecto.nombre],
    ['Tarea', 'Documentar pruebas'],
    ['Responsable del equipo', 'Ana Torres'],
    ['Fecha límite de ejemplo', '05/10/2026'],
    ['Fecha de corte', '06/10/2026'],
    ['Estado de ejemplo', 'Pendiente'],
  ]

  return (
    <>
      <Encabezado antetitulo="TA-016 · Detalle de alerta" titulo="Entregable con fecha vencida" />

      <article className="card">
        <Pill tono="warn">Ejemplo ilustrativo</Pill>
        <h3 style={{ marginTop: 'var(--sp-4)' }}>Causa y evidencia</h3>

        {datos.map(([etiqueta, valor]) => (
          <p key={etiqueta}>
            <b>{etiqueta}:</b> {valor}
          </p>
        ))}

        <p className="muted">
          Alerta independiente del conjunto de 20 tareas: escenario ilustrativo para validar el
          diseño de esta pantalla, no resultado del motor de reglas.
        </p>

        <div className="acciones">
          <Boton onClick={() => setRevisada(true)}>Marcar revisada en demo</Boton>
          <Boton variante="secundario" onClick={onVolver}>
            Volver al Dashboard
          </Boton>
        </div>

        {revisada && (
          <p role="status" style={{ marginTop: 'var(--sp-4)' }}>
            Revisada por el docente en esta demostración.
          </p>
        )}
      </article>
    </>
  )
}
