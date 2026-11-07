/** HU-001 · Inicio de sesión del docente. */
import { useEffect, useState } from 'react'
import { Aviso, Boton, Campo, Pill } from '../componentes/UI.jsx'
import { API_ACTIVA, establecerToken, iniciarSesion, obtenerEstado } from '../api.js'
import { CLAVE_DEMO, CUENTAS } from '../datos/demo.js'

export default function Login({ bloqueado = false, onEntrar }) {
  const [correo, setCorreo] = useState('')
  const [clave, setClave] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  // TA-025 · El backend gratuito se duerme tras 15 min sin uso. Al abrir el
  // login se le pide /health para que vaya despertando mientras el docente
  // escribe: verificando | listo | despertando (tarda más de 5 s) | sin_conexion
  const [servidor, setServidor] = useState(API_ACTIVA ? 'verificando' : 'listo')

  useEffect(() => {
    if (!API_ACTIVA) return undefined
    const control = new AbortController()
    const lento = setTimeout(() => setServidor(e => (e === 'verificando' ? 'despertando' : e)), 5000)
    obtenerEstado({ senal: control.signal })
      .then(() => setServidor('listo'))
      .catch(e => { if (e.name !== 'AbortError') setServidor('sin_conexion') })
      .finally(() => clearTimeout(lento))
    return () => { clearTimeout(lento); control.abort() }
  }, [])

  /** TA-039 · Con API activa la sesión la crea el servidor (POST /auth/login). */
  async function entrarConApi() {
    setEnviando(true)
    try {
      const sesion = await iniciarSesion(correo.trim(), clave)
      establecerToken(sesion.token)
      setError('')
      onEntrar(sesion.docente.correo)
    } catch (e) {
      setError(
        e.estado === 401
          ? 'Correo o contraseña incorrectos.'
          : 'No se pudo conectar con el servidor. Si estaba en reposo puede tardar hasta un minuto en despertar; inténtalo de nuevo.',
      )
      setEnviando(false)
    }
  }

  function enviar(e) {
    e.preventDefault()

    // Se distingue «faltan datos» de «credenciales incorrectas»: decirle a
    // alguien que su contraseña es incorrecta cuando ni siquiera la escribió
    // es confuso y manda a revisar donde no toca.
    if (!correo.trim() || !clave) {
      setError('Completa el correo y la contraseña para continuar.')
      return
    }
    if (API_ACTIVA) {
      entrarConApi()
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
          {servidor === 'despertando' && (
            <p className="small muted" role="status">
              Despertando el servidor; la primera conexión puede tardar hasta un minuto.
            </p>
          )}
          {servidor === 'sin_conexion' && !error && (
            <p className="small muted" role="status">
              El servidor no responde todavía. Puedes intentar ingresar de todos modos.
            </p>
          )}
          <Boton type="submit" disabled={enviando}>
            {enviando ? 'Ingresando…' : 'Ingresar'}
          </Boton>
        </form>

        {!API_ACTIVA && (
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
        )}
      </div>
    </div>
  )
}
