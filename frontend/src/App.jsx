/**
 * TA-005 · Frontend base (React)
 *
 * Orquesta el estado de la sesión, el enrutado por hash y las vistas.
 * El estado vive en memoria: se reinicia al recargar, igual que el prototipo.
 */
import { useEffect, useState } from 'react'
import './estilos/tokens.css'
import './estilos/base.css'

import Shell from './layout/Shell.jsx'
import Login from './paginas/Login.jsx'
import Proyectos from './paginas/Proyectos.jsx'
import Formulario from './paginas/Formulario.jsx'
import Detalle from './paginas/Detalle.jsx'
import Dashboard from './paginas/Dashboard.jsx'
import Historial from './paginas/Historial.jsx'
import SistemaVisual from './paginas/SistemaVisual.jsx'
import Alerta from './paginas/Alerta.jsx'
import { Aviso, Boton, Encabezado } from './componentes/UI.jsx'
import {
  API_ACTIVA, cerrarSesionApi, crearProyecto, desactivarProyecto, editarProyecto,
  establecerToken, obtenerProyectos,
} from './api.js'
import { PROYECTOS_INICIALES } from './datos/demo.js'
import { aApi, deApi } from './datos/proyectos_api.js'

const RUTAS_PRIVADAS = [
  'proyectos', 'nuevo', 'editar', 'detalle',
  'dashboard', 'historial', 'sistema', 'alerta',
]

/** Sección del menú lateral que corresponde a cada ruta. */
const SECCION = {
  proyectos: 'proyectos', nuevo: 'proyectos', editar: 'proyectos', detalle: 'proyectos',
  dashboard: 'dashboard', alerta: 'dashboard',
  historial: 'historial', sistema: 'sistema',
}

/** La ruta vive en el hash de la URL; esta es la única lectura de esa fuente. */
const rutaDeHash = () => window.location.hash.slice(1) || 'login'

export default function App() {
  const [ruta, setRuta] = useState(rutaDeHash)
  const [sesion, setSesion] = useState(null)
  // TA-039 · Con API activa los proyectos salen del servidor; si no, de la demostración.
  const [proyectos, setProyectos] = useState(API_ACTIVA ? [] : PROYECTOS_INICIALES)
  const [cargandoProyectos, setCargandoProyectos] = useState(false)
  const [actual, setActual] = useState(1)
  const [notionFallo, setNotionFallo] = useState(false)
  const [corridas, setCorridas] = useState([])
  const [ultimaCorrida, setUltimaCorrida] = useState('Sin ejecución en esta sesión')
  const [aviso, setAviso] = useState('')
  const [alertaActual, setAlertaActual] = useState(null)

  // El hash manda: cualquier cambio (navegación, atrás/adelante, enlace
  // directo) entra por aquí.
  useEffect(() => {
    const alCambiar = () => setRuta(rutaDeHash())
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])

  useEffect(() => { window.scrollTo(0, 0) }, [ruta])

  /**
   * Navega cambiando el hash, que a su vez actualiza el estado.
   *
   * Antes el estado se escribía primero y un efecto reescribía el hash para
   * igualarlo. Eso abría una carrera: si el hash cambiaba por fuera (abrir
   * una URL directa) antes de que ese efecto corriera, el efecto lo devolvía
   * al valor anterior y la navegación se perdía. Lo detectó la prueba CP-L6.
   */
  function navegar(destino) {
    if (rutaDeHash() === destino) setRuta(destino)
    else window.location.hash = destino
  }

  // El aviso flotante se oculta solo.
  useEffect(() => {
    if (!aviso) return
    const id = setTimeout(() => setAviso(''), 4000)
    return () => clearTimeout(id)
  }, [aviso])

  const proyecto = proyectos.find(p => p.id === actual) ?? proyectos[0]
  const requiereSesion = RUTAS_PRIVADAS.includes(ruta)

  function salir() {
    if (API_ACTIVA) {
      cerrarSesionApi().catch(() => {}) // la petición sale con el token antes de borrarlo
      establecerToken(null)
      setProyectos([])
    }
    setSesion(null)
    navegar('login')
  }

  async function cargarProyectos() {
    setCargandoProyectos(true)
    try {
      const lista = (await obtenerProyectos()).map(deApi)
      setProyectos(lista)
      setActual(lista[0]?.id ?? 0)
    } catch {
      setAviso('No se pudieron cargar los proyectos desde el servidor.')
    } finally {
      setCargandoProyectos(false)
    }
  }

  async function guardarProyecto(datos) {
    if (API_ACTIVA) {
      try {
        if (ruta === 'editar') {
          const p = deApi(await editarProyecto(actual, aApi(datos)))
          setProyectos(ps => ps.map(x => (x.id === p.id ? p : x)))
        } else {
          const p = deApi(await crearProyecto(aApi(datos)))
          setProyectos(ps => [...ps, p])
          if (!proyecto) setActual(p.id)
        }
      } catch (e) {
        setAviso(e.estado === 422
          ? 'El servidor rechazó los datos del proyecto. Revísalos e inténtalo de nuevo.'
          : 'No se pudo guardar el proyecto en el servidor.')
        return
      }
      navegar('proyectos')
      setAviso('Proyecto guardado en el servidor.')
      return
    }
    if (ruta === 'editar') {
      setProyectos(ps => ps.map(p => (p.id === actual ? { ...p, ...datos } : p)))
    } else {
      setProyectos(ps => [...ps, { ...datos, id: Date.now(), activo: true }])
    }
    navegar('proyectos')
    setAviso('Proyecto guardado en memoria. Se reinicia al recargar la página.')
  }

  async function alternarProyecto(id) {
    if (API_ACTIVA) {
      // El backend solo expone «desactivar» (PATCH /proyectos/{id}/desactivar).
      if (!proyectos.find(p => p.id === id)?.activo) {
        setAviso('El servidor todavía no permite reactivar un proyecto.')
        return
      }
      try {
        await desactivarProyecto(id)
        setProyectos(ps => ps.map(p => (p.id === id ? { ...p, activo: false } : p)))
        setAviso('Proyecto desactivado en el servidor.')
      } catch {
        setAviso('No se pudo desactivar el proyecto en el servidor.')
      }
      return
    }
    let activo = false
    setProyectos(ps =>
      ps.map(p => {
        if (p.id !== id) return p
        activo = !p.activo
        return { ...p, activo }
      }),
    )
    setAviso(activo
      ? 'Proyecto reactivado en la demostración.'
      : 'Proyecto desactivado en la demostración.')
  }

  function registrarCorrida(fecha) {
    setUltimaCorrida(fecha)
    setCorridas(cs => [
      { fecha, estado: notionFallo ? 'Parcial: Notion falló' : 'Completado (simulado)' },
      ...cs,
    ])
    setAviso('Simulación registrada en el historial de esta sesión.')
  }

  const bandaDemo = API_ACTIVA ? (
    <div className="demo">
      <strong>Conectado al servidor.</strong> Sesión, proyectos y evidencias son reales; los
      indicadores y las alertas siguen siendo de demostración hasta TA-040.
    </div>
  ) : (
    <div className="demo">
      <strong>Prototipo navegable · Datos simulados.</strong> Acceso exclusivo del docente. Sin
      conexión a servicios reales.
    </div>
  )

  // --- Sin sesión: solo el login -----------------------------------------
  if (!sesion) {
    return (
      <>
        {bandaDemo}
        <Login
          bloqueado={requiereSesion}
          onEntrar={correo => {
            setSesion(correo)
            if (API_ACTIVA) cargarProyectos()
            navegar('proyectos')
          }}
        />
      </>
    )
  }

  // --- Con sesión: marco + vista -----------------------------------------
  const sinProyecto = (
    <>
      <Encabezado antetitulo="Mis proyectos" titulo="Todavía no hay un proyecto seleccionado" />
      <Aviso>
        {cargandoProyectos
          ? 'Cargando tus proyectos…'
          : 'Esta vista necesita un proyecto. Registra el primero para empezar a supervisarlo.'}
      </Aviso>
      <Boton onClick={() => navegar('nuevo')}>+ Registrar proyecto</Boton>
    </>
  )

  const vistas = {
    proyectos: cargandoProyectos ? (
      <Aviso>Cargando tus proyectos…</Aviso>
    ) : (
      <Proyectos
        proyectos={proyectos}
        onAbrir={id => { setActual(id); setAlertaActual(null); navegar('detalle') }}
        onEditar={id => { setActual(id); navegar('editar') }}
        onNuevo={() => navegar('nuevo')}
        onAlternar={alternarProyecto}
      />
    ),
    nuevo: <Formulario onGuardar={guardarProyecto} onCancelar={() => navegar('proyectos')} />,
    editar: (
      <Formulario
        proyecto={proyecto}
        onGuardar={guardarProyecto}
        onCancelar={() => navegar('proyectos')}
      />
    ),
    detalle: (
      <Detalle
        proyecto={proyecto}
        notionFallo={notionFallo}
        onNotionFallo={setNotionFallo}
        onVolver={() => navegar('proyectos')}
        onDashboard={() => navegar('dashboard')}
      />
    ),
    dashboard: (
      <Dashboard
        proyecto={proyecto}
        notionFallo={notionFallo}
        ultimaCorrida={ultimaCorrida}
        onSimular={registrarCorrida}
        onAlerta={a => { setAlertaActual(a); navegar('alerta') }}
      />
    ),
    alerta: <Alerta proyecto={proyecto} alerta={alertaActual} onVolver={() => navegar('dashboard')} />,
    historial: <Historial corridas={corridas} onDashboard={() => navegar('dashboard')} />,
    sistema: <SistemaVisual onEjemplo={() => setAviso('Ejemplo del componente botón')} />,
  }

  return (
    <>
      {bandaDemo}
      <Shell ruta={SECCION[ruta] ?? 'proyectos'} email={sesion} onNavegar={navegar} onSalir={salir}>
        {!proyecto && ['editar', 'detalle', 'dashboard', 'alerta'].includes(ruta)
          ? sinProyecto
          : vistas[ruta] ?? vistas.proyectos}
      </Shell>
      {aviso && (
        <div className="toast" role="status" aria-live="polite">
          {aviso}
        </div>
      )}
    </>
  )
}
