/** HU-002 · Listado de proyectos académicos supervisados. */
import { useState } from 'react'
import { Aviso, Boton, Encabezado, Pill } from '../componentes/UI.jsx'

export default function Proyectos({ proyectos, onAbrir, onEditar, onNuevo, onAlternar }) {
  const [filtro, setFiltro] = useState('activos')
  const visibles = proyectos.filter(p => filtro === 'todos' || p.activo)

  return (
    <>
      <Encabezado
        antetitulo="HU-002 · Proyectos académicos"
        titulo="Mis proyectos"
        descripcion="Organiza las fuentes y supervisa el avance de cada equipo."
        accion={<Boton onClick={onNuevo}>+ Registrar proyecto</Boton>}
      />

      <Aviso>
        Los integrantes forman parte del equipo supervisado. No se crean cuentas ni accesos
        para ellos.
      </Aviso>

      <label style={{ maxWidth: '260px' }}>
        Mostrar
        <select value={filtro} onChange={e => setFiltro(e.target.value)}>
          <option value="activos">Proyectos activos</option>
          <option value="todos">Todos los proyectos</option>
        </select>
      </label>

      {visibles.length === 0 ? (
        <div className="card">No hay proyectos activos. Registra uno para comenzar.</div>
      ) : (
        <div className="grid dos">
          {visibles.map(p => (
            <article className="card" key={p.id}>
              <div className="head">
                <Pill tono={p.activo ? 'ok' : 'warn'}>{p.activo ? 'Activo' : 'Inactivo'}</Pill>
                <span className="small muted">{p.curso}</span>
              </div>

              <h2>{p.nombre}</h2>
              <p className="muted">{p.integrantes}</p>
              <p className="small">
                {p.inicio} → {p.fin}
              </p>

              <div className="acciones small">
                <Pill>GitHub</Pill>
                <Pill>Notion</Pill>
                <Pill>Google Drive</Pill>
              </div>

              <div className="acciones" style={{ marginTop: 'var(--sp-4)' }}>
                <Boton onClick={() => onAbrir(p.id)}>Ver proyecto</Boton>
                <Boton variante="secundario" onClick={() => onEditar(p.id)}>
                  Editar
                </Boton>
                <Boton variante="secundario" onClick={() => onAlternar(p.id)}>
                  {p.activo ? 'Desactivar' : 'Reactivar'}
                </Boton>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  )
}
