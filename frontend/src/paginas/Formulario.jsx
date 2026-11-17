/** HU-002 · Alta y edición de un proyecto académico. */
import { useState } from 'react'
import { Aviso, Boton, Campo, Encabezado } from '../componentes/UI.jsx'

const VACIO = {
  nombre: '', curso: '', inicio: '', fin: '', integrantes: '',
  github: '', notion: '', drive: '', url: '', selector: '',
}

// Drive es opcional: hay equipos que no usan una carpeta compartida.
const OPCIONALES = ['drive']

const esURL = valor => {
  try {
    return ['http:', 'https:'].includes(new URL(valor).protocol)
  } catch {
    return false
  }
}

export default function Formulario({ proyecto, onGuardar, onCancelar }) {
  const [datos, setDatos] = useState({ ...VACIO, ...(proyecto || {}) })
  const [error, setError] = useState('')
  const [invalidos, setInvalidos] = useState({})
  const editando = Boolean(proyecto)

  const campo = (clave, etiqueta, type = 'text', ayuda) => (
    <Campo
      etiqueta={etiqueta}
      type={type}
      name={clave}
      required={!OPCIONALES.includes(clave)}
      aria-invalid={invalidos[clave] ? 'true' : undefined}
      ayuda={ayuda}
      value={datos[clave] ?? ''}
      onChange={e => setDatos({ ...datos, [clave]: e.target.value })}
    />
  )

  function enviar(e) {
    e.preventDefault()
    const limpio = Object.fromEntries(
      Object.keys(VACIO).map(k => [k, String(datos[k] ?? '').trim()]),
    )

    // TA-031 · H3: se validan todos los campos a la vez, se marcan los inválidos
    // (aria-invalid) y el foco va al primero.
    const errs = {}
    const mensajes = []
    const marcar = (claves, msg) => {
      claves.forEach(k => { errs[k] = true })
      mensajes.push(msg)
    }
    if (!limpio.nombre) marcar(['nombre'], 'El nombre del proyecto es obligatorio.')
    const faltan = Object.entries(limpio)
      .filter(([k, v]) => !v && k !== 'nombre' && k !== 'integrantes' && !OPCIONALES.includes(k))
      .map(([k]) => k)
    if (faltan.length) marcar(faltan, 'Completa todos los campos obligatorios.')
    if (!limpio.integrantes.split(',').some(v => v.trim())) {
      marcar(['integrantes'], 'Registra al menos un integrante.')
    }
    if (limpio.inicio && limpio.fin && limpio.inicio > limpio.fin) {
      marcar(['fin'], 'La fecha de fin debe ser igual o posterior a la fecha de inicio.')
    }
    const urlsMalas = ['github', 'notion', 'url', 'drive'].filter(k => limpio[k] && !esURL(limpio[k]))
    if (urlsMalas.length) {
      marcar(urlsMalas, 'Las referencias de fuentes y la URL pública deben ser direcciones HTTP o HTTPS válidas.')
    }

    if (mensajes.length) {
      setInvalidos(errs)
      setError(mensajes.join(' '))
      const primero = Object.keys(VACIO).find(k => errs[k])
      requestAnimationFrame(() => e.target.elements[primero]?.focus())
      return
    }

    setInvalidos({})
    setError('')
    onGuardar(limpio)
  }

  return (
    <>
      <Encabezado
        antetitulo={`Mis proyectos / ${editando ? 'Editar' : 'Registrar'} proyecto`}
        titulo={editando ? 'Editar proyecto' : 'Registrar proyecto académico'}
        descripcion="Todos los campos son obligatorios salvo la carpeta de Google Drive. El equipo se registra como información del proyecto."
        accion={
          <Boton variante="secundario" onClick={onCancelar}>
            Volver a Mis proyectos
          </Boton>
        }
      />

      <form onSubmit={enviar} noValidate>
        <article className="card">
          <h3>1. Datos del proyecto</h3>
          <div className="grid dos">
            {campo('nombre', 'Nombre del proyecto')}
            {campo('curso', 'Curso')}
            {campo('inicio', 'Fecha de inicio', 'date')}
            {campo('fin', 'Fecha de fin', 'date')}
          </div>
          <Campo
            etiqueta="Integrantes del equipo (al menos uno; separados por coma)"
            as="textarea"
            name="integrantes"
            required
            aria-invalid={invalidos.integrantes ? 'true' : undefined}
            value={datos.integrantes}
            onChange={e => setDatos({ ...datos, integrantes: e.target.value })}
          />
        </article>

        <article className="card">
          <h3>2. Fuentes de evidencia</h3>
          {campo('github', 'Repositorio de GitHub', 'url')}
          {campo('notion', 'Base de tareas de Notion', 'url')}
          {campo(
            'drive',
            'Carpeta de Google Drive (opcional)',
            'url',
            'Déjalo vacío si el equipo no usa Drive: no se evalúa la regla R4 y la fuente aparece como «No configurada».',
          )}
        </article>

        <article className="card">
          <h3>3. Aplicación a verificar</h3>
          <div className="grid dos">
            {campo('url', 'URL pública de la aplicación', 'url')}
            {campo('selector', 'Elemento a verificar (selector CSS)')}
          </div>
          <p className="small muted">
            Ejemplo: h1 o #formulario-login. La verificación automática se representa con datos
            simulados.
          </p>
        </article>

        {error && <Aviso tipo="error">{error}</Aviso>}

        <div className="acciones">
          <Boton type="submit">Guardar proyecto</Boton>
          <Boton variante="secundario" type="button" onClick={() => setDatos({ ...VACIO, ...(proyecto || {}) })}>
            Limpiar cambios
          </Boton>
        </div>
      </form>
    </>
  )
}
