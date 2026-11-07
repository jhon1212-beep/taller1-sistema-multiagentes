/**
 * TA-016 · Detalle de una alerta con su causa y evidencia.
 * HU-007 · La alerta es una de R1–R4: se muestra la regla, la explicación y el
 * registro de origen (tarea, commit o documento) que la disparó.
 */
import { useState } from 'react'
import { Aviso, Boton, Encabezado, Pill, fechaCorta } from '../componentes/UI.jsx'
import { FECHA_CORTE, DESCRIPCION_REGLAS } from '../datos/demo_supervision.js'
import { REGLAS, fechaHoraUtc } from '../datos/indicadores.js'
import { API_ACTIVA } from '../api.js'
import { textoCorte } from '../datos/supervision_api.js'

/** Filas «etiqueta: valor» de la evidencia, según de qué fuente venga. */
function filasEvidencia(ev) {
  if (ev.tipo === 'tarea') {
    return [
      ['Tarea', ev.titulo],
      ['Responsable del equipo', ev.responsable ?? 'Sin responsable'],
      ['Estado', ev.estado],
      ['Fecha límite', ev.fecha_limite ? fechaCorta(ev.fecha_limite) : 'Sin fecha límite'],
      ['Última edición', fechaHoraUtc(ev.fecha)],
      ['Identificador', ev.id],
    ]
  }
  if (ev.tipo === 'commit') {
    return [
      ['Último commit', ev.titulo],
      ['Autor', ev.responsable],
      ['Fecha', fechaHoraUtc(ev.fecha)],
      ['SHA corto', ev.sha],
    ]
  }
  return [
    ['Último documento modificado', ev.titulo],
    ['Último editor', ev.responsable],
    ['Última modificación', fechaHoraUtc(ev.fecha)],
    ['Tipo de archivo', ev.tipo_archivo ?? '—'],
    ['Identificador', ev.id],
  ]
}

export default function Alerta({ proyecto, alerta, onVolver }) {
  const [revisada, setRevisada] = useState(false)

  if (!alerta) {
    return (
      <>
        <Encabezado antetitulo="Dashboard / Detalle de alerta" titulo="Detalle de alerta" />
        <Aviso>Elige una alerta en el Dashboard para ver su explicación y su evidencia.</Aviso>
        <Boton variante="secundario" onClick={onVolver}>
          Volver al Dashboard
        </Boton>
      </>
    )
  }

  const regla = REGLAS[alerta.regla]
  // TA-040 · Con la API, la alerta trae el día de su corte; en la demo, el corte fijo del dataset.
  const corte = alerta.fecha_corte ? textoCorte(alerta.fecha_corte) : fechaHoraUtc(FECHA_CORTE)
  const origen = alerta.origen_explicacion === 'gemini' ? 'Gemini' : 'plantilla'

  return (
    <>
      <Encabezado
        antetitulo={`Dashboard / Detalle de alerta · ${alerta.regla}`}
        titulo={regla.titulo}
        descripcion={`${proyecto.nombre} · fecha de corte ${corte}`}
      />

      <article className="card" aria-labelledby="alerta-explicacion">
        <div className="alerta-cab">
          <Pill>Regla {alerta.regla}</Pill>
          <Pill>{regla.fuente}</Pill>
          <Pill>Explicación: {origen}</Pill>
        </div>

        <h2 id="alerta-explicacion">¿Por qué se generó?</h2>
        <p>{DESCRIPCION_REGLAS[alerta.regla]}</p>
        <p className="explicacion">{alerta.explicacion}</p>
        <p className="small muted">
          La alerta describe una situación del proyecto a partir de la evidencia; no asigna notas
          ni juzga a ningún estudiante.
        </p>
      </article>

      <article className="card" aria-labelledby="alerta-evidencia">
        <h2 id="alerta-evidencia">Evidencia de origen</h2>
        {filasEvidencia(alerta.evidencia).map(([etiqueta, valor]) => (
          <p key={etiqueta}>
            <b>{etiqueta}:</b> {valor}
          </p>
        ))}
        {alerta.evidencia.enlace && (
          <p>
            <a href={alerta.evidencia.enlace} target="_blank" rel="noopener noreferrer">
              Abrir la evidencia en {regla.fuente}
            </a>
          </p>
        )}

        <div className="acciones">
          <Boton onClick={() => setRevisada(true)}>
            {API_ACTIVA ? 'Marcar revisada' : 'Marcar revisada en demo'}
          </Boton>
          <Boton variante="secundario" onClick={onVolver}>
            Volver al Dashboard
          </Boton>
        </div>

        {revisada && (
          <p role="status" style={{ marginTop: 'var(--sp-4)' }}>
            {API_ACTIVA
              ? 'Marcada como revisada en esta sesión.'
              : 'Revisada por el docente en esta demostración.'}
          </p>
        )}
      </article>
    </>
  )
}
