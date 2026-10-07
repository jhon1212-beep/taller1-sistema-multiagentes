/** HU-003 / HU-004 · Detalle del proyecto con sus fuentes de evidencia. */
import { useState } from 'react'
import { Aviso, Boton, Encabezado, Estadistica, Pill, Tabla, Tabs } from '../componentes/UI.jsx'
import { COMMITS, DOCUMENTOS, TAREAS, tonoEstado } from '../datos/demo.js'

const PESTANAS = {
  resumen: 'Resumen',
  github: 'GitHub',
  notion: 'Notion',
  drive: 'Google Drive',
  validacion: 'Validación web',
}

const NOTA_DEMO = (
  <p className="small muted">
    Conjunto de ejemplo, sin consulta a una API real. La coincidencia con datos de origen se
    verifica en integración.
  </p>
)

export default function Detalle({ proyecto, notionFallo, onNotionFallo, onVolver, onDashboard }) {
  const [pestana, setPestana] = useState('resumen')

  return (
    <>
      <Encabezado
        antetitulo="Mis proyectos / Detalle"
        titulo={proyecto.nombre}
        descripcion={`${proyecto.curso} · ${proyecto.integrantes}`}
        accion={
          <Boton variante="secundario" onClick={onVolver}>
            Mis proyectos
          </Boton>
        }
      />

      <Tabs opciones={PESTANAS} activa={pestana} onCambio={setPestana} />

      {pestana === 'resumen' && (
        <>
          <div className="grid cuatro">
            <Estadistica etiqueta="Commits de ejemplo" valor="20" />
            <Estadistica etiqueta="Tareas terminadas" valor="8 / 20" />
            <Estadistica etiqueta="Documentos de ejemplo" valor="10" />
            <Estadistica etiqueta="Fuentes previstas" valor="3" />
          </div>

          <div className="grid dos">
            <article className="card">
              <h3>Fuentes del proyecto</h3>
              {[
                ['GitHub', proyecto.github],
                ['Notion', proyecto.notion],
                ['Drive', proyecto.drive],
              ].map(([nombre, enlace]) => (
                <div className="fuente" key={nombre}>
                  <b>{nombre}</b>
                  <a href={enlace} target="_blank" rel="noopener noreferrer">
                    {enlace}
                  </a>
                </div>
              ))}
            </article>

            <article className="card">
              <h3>Configuración de supervisión</h3>
              <p>
                <b>Periodo:</b> {proyecto.inicio} a {proyecto.fin}
              </p>
              <p>
                <b>URL pública:</b> {proyecto.url}
              </p>
              <p>
                <b>Elemento:</b> <code>{proyecto.selector}</code>
              </p>
              <Pill>Datos del proyecto, sin cuentas para integrantes</Pill>
            </article>
          </div>

          <Boton onClick={onDashboard}>Ver Dashboard</Boton>
        </>
      )}

      {pestana === 'github' && (
        <article className="card">
          <div className="head">
            <div>
              <div className="eyebrow">HU-003 · CP-06</div>
              <h2>Commits de GitHub</h2>
              <p className="muted">Últimos 20 commits del conjunto de demostración.</p>
            </div>
            <Pill tono="ok">20 de 20 mostrados</Pill>
          </div>
          {NOTA_DEMO}
          <Tabla
            columnas={['Autor', 'Fecha', 'Mensaje', 'SHA corto']}
            filas={COMMITS.map(c => [c.autor, c.fecha, c.mensaje, <code key={c.sha}>{c.sha}</code>])}
          />
        </article>
      )}

      {pestana === 'notion' && (
        <article className="card">
          <div className="head">
            <div>
              <div className="eyebrow">HU-004 · CP-07 / CP-08</div>
              <h2>Tareas de Notion</h2>
              <p className="muted">Responsables, estados y fechas límite del equipo.</p>
            </div>
            <Boton
              variante={notionFallo ? 'secundario' : 'peligro'}
              onClick={() => onNotionFallo(!notionFallo)}
            >
              {notionFallo ? 'Restaurar integración demo' : 'Simular token inválido'}
            </Boton>
          </div>
          {NOTA_DEMO}

          {notionFallo ? (
            <>
              <Aviso tipo="error">
                <b>Integración fallida: Notion</b>
                <br />
                El servicio rechazó las credenciales (401/403 simulado). No se cargaron tareas
                nuevas.
              </Aviso>
              <p>
                Revisa la configuración de la integración y vuelve a intentarlo. Las credenciales
                se administran fuera del prototipo.
              </p>
            </>
          ) : (
            <>
              <Pill tono="ok">20 tareas de demostración</Pill>
              <Tabla
                columnas={['Tarea', 'Responsable', 'Estado', 'Fecha límite']}
                filas={TAREAS.map(t => [
                  t.titulo,
                  t.responsable,
                  <Pill key={t.titulo} tono={tonoEstado(t.estado)}>
                    {t.estado}
                  </Pill>,
                  t.vence,
                ])}
              />
            </>
          )}
        </article>
      )}

      {pestana === 'drive' && (
        <article className="card">
          <div className="eyebrow">TA-014 · Vista anticipada</div>
          <h2>Documentación de Google Drive</h2>
          {NOTA_DEMO}
          <Tabla
            columnas={['Nombre', 'Último editor', 'Última modificación', 'Tipo']}
            filas={DOCUMENTOS.map(d => [d.nombre, d.editor, d.modificado, d.tipo])}
          />
        </article>
      )}

      {pestana === 'validacion' && (
        <article className="card">
          <h2>Verificación de la aplicación</h2>
          <p>
            <b>URL registrada:</b> {proyecto.url}
          </p>
          <p>
            <b>Elemento esperado:</b> <code>{proyecto.selector}</code>
          </p>
          <Aviso>
            Vista anticipada: aquí se mostrará el resultado de la verificación ejecutada fuera del
            prototipo.
          </Aviso>
          <Pill tono="warn">Sin ejecución real</Pill>
        </article>
      )}
    </>
  )
}
