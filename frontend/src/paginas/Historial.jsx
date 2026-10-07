/** TA-016 · Historial de ejecuciones simuladas de la sesión. */
import { Boton, Encabezado, Tabla } from '../componentes/UI.jsx'

export default function Historial({ corridas, onDashboard }) {
  return (
    <>
      <Encabezado
        antetitulo="TA-016 · Historial"
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
