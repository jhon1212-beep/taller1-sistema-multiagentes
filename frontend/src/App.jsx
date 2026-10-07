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
import { PROYECTOS_INICIALES } from './datos/demo.js'

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

export default function App() {
  const [ruta, setRuta] = useState(() => window.location.hash.slice(1) || 'login')
  const [sesion, setSesion] = useState(null)
  const [proyectos, setProyectos] = useState(PROYECTOS_INICIALES)
  const [actual, setActual] = useState(1)
  const [notionFallo, setNotionFallo] = useState(false)
  const [corridas, setCorridas] = useState([])
  const [ultimaCorrida, setUltimaCorrida] = useState('Sin ejecución en esta sesión')
  const [aviso, setAviso] = useState('')

  // Sincroniza la ruta con el hash del navegador (atrás/adelante incluidos).
  useEffect(() => {
    const alCambiar = () => setRuta(window.location.hash.slice(1) || 'login')
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])

  useEffect(() => {
    if (window.location.hash.slice(1) !== ruta) window.location.hash = ruta
    window.scrollTo(0, 0)
  }, [ruta])

  // El aviso flotante se oculta solo.
  useEffect(() => {
    if (!aviso) return
    const id = setTimeout(() => setAviso(''), 4000)
    return () => clearTimeout(id)
  }, [aviso])

  const proyecto = proyectos.find(p => p.id === actual) ?? proyectos[0]
  const requiereSesion = RUTAS_PRIVADAS.includes(ruta)

  function salir() {
    setSesion(null)
    setRuta('login')
  }

  function guardarProyecto(datos) {
    if (ruta === 'editar') {
      setProyectos(ps => ps.map(p => (p.id === actual ? { ...p, ...datos } : p)))
    } else {
      setProyectos(ps => [...ps, { ...datos, id: Date.now(), activo: true }])
    }
    setRuta('proyectos')
    setAviso('Proyecto guardado en memoria. Se reinicia al recargar la página.')
  }

  function alternarProyecto(id) {
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

  const bandaDemo = (
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
            setRuta('proyectos')
          }}
        />
      </>
    )
  }

  // --- Con sesión: marco + vista -----------------------------------------
  const vistas = {
    proyectos: (
      <Proyectos
        proyectos={proyectos}
        onAbrir={id => { setActual(id); setRuta('detalle') }}
        onEditar={id => { setActual(id); setRuta('editar') }}
        onNuevo={() => setRuta('nuevo')}
        onAlternar={alternarProyecto}
      />
    ),
    nuevo: <Formulario onGuardar={guardarProyecto} onCancelar={() => setRuta('proyectos')} />,
    editar: (
      <Formulario
        proyecto={proyecto}
        onGuardar={guardarProyecto}
        onCancelar={() => setRuta('proyectos')}
      />
    ),
    detalle: (
      <Detalle
        proyecto={proyecto}
        notionFallo={notionFallo}
        onNotionFallo={setNotionFallo}
        onVolver={() => setRuta('proyectos')}
        onDashboard={() => setRuta('dashboard')}
      />
    ),
    dashboard: (
      <Dashboard
        proyecto={proyecto}
        notionFallo={notionFallo}
        ultimaCorrida={ultimaCorrida}
        onSimular={registrarCorrida}
        onAlerta={() => setRuta('alerta')}
      />
    ),
    alerta: <Alerta proyecto={proyecto} onVolver={() => setRuta('dashboard')} />,
    historial: <Historial corridas={corridas} onDashboard={() => setRuta('dashboard')} />,
    sistema: <SistemaVisual onEjemplo={() => setAviso('Ejemplo del componente botón')} />,
  }

  return (
    <>
      {bandaDemo}
      <Shell ruta={SECCION[ruta] ?? 'proyectos'} email={sesion} onNavegar={setRuta} onSalir={salir}>
        {vistas[ruta] ?? vistas.proyectos}
      </Shell>
      {aviso && (
        <div className="toast" role="status" aria-live="polite">
          {aviso}
        </div>
      )}
    </>
  )
}
