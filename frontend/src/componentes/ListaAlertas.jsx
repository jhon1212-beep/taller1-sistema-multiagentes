/** HU-007 · Lista de alertas R1–R4, filtrable por regla (demo y API usan la misma). */
import { useState } from 'react'
import { Boton, Pill } from './UI.jsx'
import { REGLAS } from '../datos/indicadores.js'

export default function ListaAlertas({ alertas, onAlerta }) {
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

