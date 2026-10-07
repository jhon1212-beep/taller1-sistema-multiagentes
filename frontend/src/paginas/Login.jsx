/** HU-001 · Inicio de sesión del docente. */
import { useState } from 'react'
import { Aviso, Boton, Campo, Pill } from '../componentes/UI.jsx'
import { CLAVE_DEMO, CUENTAS } from '../datos/demo.js'

export default function Login({ bloqueado = false, onEntrar }) {
  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [error, setError] = useState('')

  function enviar(e) {
    e.preventDefault()

    // Se distingue «faltan datos» de «credenciales incorrectas»: decirle a
    // alguien que su contraseña es incorrecta cuando ni siquiera la escribió
    // es confuso y manda a revisar donde no toca.
    if (!correo.trim() || !clave) {
      setError('Completa el correo y la contraseña para continuar.')
      return
    }
    if (CUENTAS.includes(correo.trim()) && clave === CLAVE_DEMO) {
      setError('')
      onEntrar(correo.trim())
      return
    }
    setError('Correo o contraseña incorrectos.')
  }

  return (
    <div className="login-wrap">
      <div className="login-intro">
        <div className="eyebrow">Supervisión de proyectos</div>
        <h1>La evidencia de tus proyectos, en un solo lugar.</h1>
        <p className="muted">
          Consulta la actividad del equipo y decide dónde acompañar su trabajo.
        </p>
        <ul>
          <li>Commits de GitHub con autor y fecha.</li>
          <li>Tareas y responsables desde Notion.</li>
          <li>Documentos, alertas y seguimiento por proyecto.</li>
        </ul>
        <Pill>HU-001 · Inicio de sesión docente</Pill>
      </div>

      <div className="card login-card">
        <h2>Iniciar sesión</h2>
        <p className="muted">Accede a los proyectos que supervisas.</p>

        {bloqueado && (
          <Aviso tipo="error">
            Debes iniciar sesión para acceder a Mis proyectos. Estado visual equivalente a
            acceso no autorizado; no es una respuesta HTTP real.
          </Aviso>
        )}

        <form onSubmit={enviar} noValidate aria-label="Inicio de sesión del docente">
          <Campo
            etiqueta="Correo del docente"
            type="email"
            autoComplete="username"
            required
            autoFocus
            placeholder="docente1@demo.test"
            value={correo}
            onChange={e => setCorreo(e.target.value)}
          />
          <Campo
            etiqueta="Contraseña"
            type="password"
            autoComplete="current-password"
            required
            placeholder="Contraseña de demostración"
            value={clave}
            onChange={e => setClave(e.target.value)}
          />
          {error && <Aviso tipo="error">{error}</Aviso>}
          <Boton type="submit">Ingresar</Boton>
        </form>

        <div className="login-foot">
          <strong>Recorrido de demostración</strong>
          <br />
          Correo: docente1@demo.test
          <br />
          Contraseña: {CLAVE_DEMO}
          <br />
          <span className="muted">
            Cuentas ficticias docente1 a docente5. No ingreses credenciales reales.
          </span>
        </div>
      </div>
    </div>
  )
}
