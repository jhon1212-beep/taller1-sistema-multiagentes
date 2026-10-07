/** EN-UI-001 · Muestrario del sistema visual compartido. */
import { Boton, Campo, Encabezado, Pill, Tabla } from '../componentes/UI.jsx'

const COLORES = [
  ['brand', 'Marca'],
  ['brand2', 'Acción'],
  ['ok', 'Éxito'],
  ['warn', 'Atención'],
  ['bad', 'Error'],
]

const ESCALA = [
  ['--fs-kpi', '26px', 'Cifras KPI y título de página'],
  ['--fs-h2', '21px', 'Título de sección'],
  ['--fs-lg', '15px', 'Subtítulo'],
  ['--fs-h3', '14.5px', 'Título de tarjeta'],
  ['--fs-base', '14px', 'Cuerpo'],
  ['--fs-sm', '12.5px', 'Texto de apoyo'],
  ['--fs-xs', '11.5px', 'Etiquetas y antetítulos'],
]

export default function SistemaVisual({ onEjemplo }) {
  return (
    <>
      <Encabezado
        antetitulo="EN-UI-001 · Sistema visual"
        titulo="Diseño compartido"
        descripcion="Tokens y componentes que consumen todas las vistas."
      />

      <article className="card">
        <h3>Cinco colores de referencia</h3>
        <div className="muestras">
          {COLORES.map(([token, etiqueta]) => (
            <div className="muestra" key={token} style={{ background: `var(--${token})` }}>
              {etiqueta}
              <br />
              <code>--{token}</code>
            </div>
          ))}
        </div>
        <p className="small muted" style={{ marginTop: 'var(--sp-4)' }}>
          Superficies, bordes y textos consumen también los tokens semánticos.
        </p>
      </article>

      <article className="card">
        <h3>Escala tipográfica</h3>
        <Tabla columnas={['Token', 'Tamaño', 'Uso']} filas={ESCALA.map(f => [<code key={f[0]}>{f[0]}</code>, f[1], f[2]])} />
      </article>

      <article className="card">
        <h3>Componentes base</h3>
        <div className="acciones">
          <Boton onClick={onEjemplo}>Botón</Boton>
          <Boton variante="secundario">Secundario</Boton>
          <Boton variante="peligro">Peligro</Boton>
          <Pill tono="ok">ok</Pill>
          <Pill tono="warn">warn</Pill>
          <Pill tono="bad">bad</Pill>
          <Pill>neutro</Pill>
        </div>
        <Campo etiqueta="Campo de formulario" placeholder="Ejemplo de campo" />
        <p className="small muted">
          Tarjeta, tabla, pestañas, barra de progreso y aviso completan el conjunto base.
        </p>
      </article>
    </>
  )
}
