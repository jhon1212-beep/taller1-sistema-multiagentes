/** HU-002 · Alta y edición de un proyecto académico. */
import { useState } from 'react'
import { Aviso, Boton, Campo, Encabezado } from '../componentes/UI.jsx'

const VACIO = {
  nombre: '', curso: '', inicio: '', fin: '', integrantes: '',
  github: '', notion: '', drive: '', url: '', selector: '',
}

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
  const editando = Boolean(proyecto)

  const campo = (clave, etiqueta, type = 'text') => (
    <Campo
      etiqueta={etiqueta}
      type={type}
      required
      value={datos[clave] ?? ''}
      onChange={e => setDatos({ ...datos, [clave]: e.target.value })}
    />
  )

  function enviar(e) {
    e.preventDefault()
    const limpio = Object.fromEntries(
      Object.keys(VACIO).map(k => [k, String(datos[k] ?? '').trim()]),
    )

    if (!limpio.nombre) {
      return setError('El nombre del proyecto es obligatorio. No se guardó el proyecto.')
    }
    if (Object.values(limpio).some(v => !v) || !limpio.integrantes.split(',').some(v => v.trim())) {
      return setError('Completa todos los campos y registra al menos un integrante.')
    }
    if (limpio.inicio > limpio.fin) {
      return setError('La fecha de fin debe ser igual o posterior a la fecha de inicio.')
    }
    if (!['github', 'notion', 'drive', 'url'].every(k => esURL(limpio[k]))) {
      return setError(
        'Las referencias de fuentes y la URL pública deben ser direcciones HTTP o HTTPS válidas.',
      )
    }

    setError('')
    onGuardar(limpio)
  }

  return (
    <>
      <Encabezado
        antetitulo={`HU-002 · ${editando ? 'Editar' : 'Registrar'} proyecto`}
        titulo={editando ? 'Editar proyecto' : 'Registrar proyecto académico'}
        descripcion="Todos los campos son obligatorios. El equipo se registra como información del proyecto."
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
            required
            value={datos.integrantes}
            onChange={e => setDatos({ ...datos, integrantes: e.target.value })}
          />
        </article>

        <article className="card">
          <h3>2. Fuentes de evidencia</h3>
          {campo('github', 'Repositorio de GitHub', 'url')}
          {campo('notion', 'Base de tareas de Notion', 'url')}
          {campo('drive', 'Carpeta de Google Drive', 'url')}
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
