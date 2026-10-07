/** TA-005 · Marco de la aplicación: barra lateral + contenido. */
import { Boton } from '../componentes/UI.jsx'

const SECCIONES = [
  ['proyectos', 'Mis proyectos'],
  ['dashboard', 'Dashboard'],
  ['historial', 'Historial'],
  ['sistema', 'Sistema visual'],
]

export default function Shell({ ruta, email, onNavegar, onSalir, children }) {
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          ◈ AgenteSeguimiento
          <small>Supervisión académica</small>
        </div>

        <nav aria-label="Navegación docente">
          {SECCIONES.map(([id, etiqueta]) => (
            <button
              key={id}
              aria-current={ruta === id ? 'page' : undefined}
              onClick={() => onNavegar(id)}
            >
              {etiqueta}
            </button>
          ))}
        </nav>

        <div className="perfil">
          <b>Cuenta docente</b>
          <small>{email}</small>
          <Boton variante="secundario" onClick={onSalir} style={{ marginTop: 'var(--sp-4)' }}>
            Cerrar sesión
          </Boton>
        </div>
      </aside>

      <main>
        {children}
        <div className="pie">
          Maqueta con datos de demostración · Las acciones representan el flujo propuesto.
        </div>
      </main>
    </div>
  )
}
