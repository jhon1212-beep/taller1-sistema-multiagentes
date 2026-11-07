/** HU-003 / HU-004 · Detalle del proyecto con sus fuentes de evidencia. */
import { useEffect, useState } from 'react'
import {
  API_ACTIVA, ejecutarValidacion, obtenerCommits, obtenerDocumentos, obtenerTareas, obtenerValidaciones,
} from '../api.js'
import { Aviso, Boton, Encabezado, Estadistica, Pill, Tabla, Tabs, fechaCorta } from '../componentes/UI.jsx'
import { COMMITS, DOCUMENTOS, TAREAS, tonoEstado } from '../datos/demo.js'
import { fechaCorta16 } from '../datos/proyectos_api.js'
import { fechaHoraUtc } from '../datos/indicadores.js'
import { mensajeError } from '../datos/supervision_api.js'

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

/** HU-004 · Tareas de Notion leídas de la API del backend (GET /proyectos/{id}/tareas). */
function TareasNotionApi({ proyecto }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const control = new AbortController()
    setDatos(null)
    setError(null)
    obtenerTareas(proyecto.id, { senal: control.signal })
      .then(setDatos)
      .catch(e => {
        if (e.name !== 'AbortError') setError(e.message)
      })
    return () => control.abort()
  }, [proyecto.id])

  return (
    <article className="card">
      <div className="head">
        <div>
          <div className="eyebrow">HU-004 · CP-07 / CP-08</div>
          <h2>Tareas de Notion</h2>
          <p className="muted">Responsables, estados y fechas límite del equipo.</p>
        </div>
        {datos?.estado === 'ok' && <Pill tono="ok">{datos.total} tareas</Pill>}
      </div>

      {!datos && !error && <p className="muted">Cargando tareas…</p>}

      {error && (
        <Aviso tipo="error">
          <b>No se pudo consultar el servidor</b>
          <br />
          {error}
        </Aviso>
      )}

      {datos?.estado === 'fallo' && (
        <Aviso tipo="error">
          <b>Integración fallida: Notion</b>
          <br />
          {datos.error.replace(/^Integración fallida:\s*/, '')}
        </Aviso>
      )}

      {datos?.estado === 'ok' && (
        <>
          <p className="small muted">
            Terminadas: {datos.resumen.listo} · En curso: {datos.resumen.en_curso} · Sin empezar:{' '}
            {datos.resumen.sin_empezar} · Sin responsable: {datos.resumen.sin_responsable}
          </p>
          <Tabla
            columnas={['Tarea', 'Responsable', 'Estado', 'Fecha límite']}
            filas={datos.tareas.map(t => [
              t.tarea,
              t.responsable ?? 'Sin responsable',
              <Pill key={t.id} tono={t.estado === 'Listo' ? 'ok' : t.estado === 'En curso' ? 'warn' : 'neutro'}>
                {t.estado ?? 'Sin estado'}
              </Pill>,
              t.fecha_limite ?? '—',
            ])}
          />
        </>
      )}
    </article>
  )
}

/** TA-039 · Lee una lista del backend y la cancela si cambia el proyecto o se cierra la vista. */
function useConsulta(consulta, proyectoId) {
  const [estado, setEstado] = useState({ datos: null, error: null })
  useEffect(() => {
    const control = new AbortController()
    setEstado({ datos: null, error: null })
    consulta(proyectoId, { senal: control.signal })
      .then(datos => setEstado({ datos, error: null }))
      .catch(e => {
        if (e.name !== 'AbortError') setEstado({ datos: null, error: e.message })
      })
    return () => control.abort()
  }, [consulta, proyectoId])
  return estado
}

/** Tarjeta común de una fuente leída de la API: cabecera, carga, error y tabla. */
function FuenteApi({ eyebrow, titulo, descripcion, unidad, estado, columnas, filas }) {
  const { datos, error } = estado
  return (
    <article className="card">
      <div className="head">
        <div>
          <div className="eyebrow">{eyebrow}</div>
          <h2>{titulo}</h2>
          <p className="muted">{descripcion}</p>
        </div>
        {datos && <Pill tono={datos.estado_fuente === 'ok' ? 'ok' : 'warn'}>{datos.total} {unidad}</Pill>}
      </div>

      {!datos && !error && <p className="muted">Cargando…</p>}

      {error && (
        <Aviso tipo="error">
          <b>No se pudo consultar el servidor</b>
          <br />
          {error}
        </Aviso>
      )}

      {datos && datos.estado_fuente !== 'ok' && (
        <Aviso>La fuente todavía no se ha sincronizado con éxito; se muestra lo último guardado.</Aviso>
      )}

      {datos && <Tabla columnas={columnas} filas={filas(datos.items)} vacio="Todavía no hay registros guardados." />}
    </article>
  )
}

function CommitsApi({ proyecto }) {
  const estado = useConsulta(obtenerCommits, proyecto.id)
  return (
    <FuenteApi
      eyebrow="HU-003 · CP-06"
      titulo="Commits de GitHub"
      descripcion="Últimos commits guardados del proyecto, del más reciente al más antiguo. Fechas en UTC."
      unidad="commits"
      estado={estado}
      columnas={['Autor', 'Fecha', 'Mensaje', 'SHA corto']}
      filas={items => items.map(c => [c.autor, fechaCorta16(c.fecha), c.mensaje, <code key={c.sha}>{c.sha.slice(0, 7)}</code>])}
    />
  )
}

function DocumentosApi({ proyecto }) {
  const estado = useConsulta(obtenerDocumentos, proyecto.id)
  return (
    <FuenteApi
      eyebrow="HU-005 · CP-04"
      titulo="Documentación de Google Drive"
      descripcion="Documentos guardados de la carpeta del proyecto, del más reciente al más antiguo. Fechas en UTC."
      unidad="documentos"
      estado={estado}
      columnas={['Nombre', 'Último editor', 'Última modificación', 'Tipo']}
      filas={items => items.map(d => [d.nombre, d.ultimo_editor, fechaCorta16(d.fecha), d.tipo ?? '—'])}
    />
  )
}

/**
 * HU-008 / TA-044 · Validación funcional CP-17 leída de la API.
 * Muestra el último resultado y el historial; «Ejecutar validación» dispara el
 * workflow e2e.yml (TA-021) y muestra «en ejecución» hasta recibir el resultado.
 */
function ValidacionApi({ proyecto }) {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  const [ejecutando, setEjecutando] = useState(false)

  useEffect(() => {
    const control = new AbortController()
    setDatos(null)
    setError('')
    obtenerValidaciones(proyecto.id, { senal: control.signal })
      .then(setDatos)
      .catch(e => { if (e.name !== 'AbortError') setError(mensajeError(e, 'No se pudo leer la validación')) })
    return () => control.abort()
  }, [proyecto.id])

  async function ejecutar() {
    setEjecutando(true)
    setError('')
    try {
      const nueva = await ejecutarValidacion(proyecto.id)
      setDatos(d => ({
        ...d,
        resumen: { ...d?.resumen, [nueva.resultado]: (d?.resumen?.[nueva.resultado] ?? 0) + 1 },
        items: [nueva, ...(d?.items ?? [])],
      }))
    } catch (e) {
      setError(mensajeError(e, 'No se pudo ejecutar la validación'))
    } finally {
      setEjecutando(false)
    }
  }

  const ultima = datos?.items?.[0]

  return (
    <article className="card">
      <div className="head">
        <div>
          <div className="eyebrow">HU-008 · CP-17</div>
          <h2>Verificación de la aplicación</h2>
          <p className="muted">
            <b>URL registrada:</b> {proyecto.url} · <b>Elemento esperado:</b> <code>{proyecto.selector}</code>
          </p>
        </div>
        <Boton onClick={ejecutar} disabled={ejecutando || !proyecto.activo}>
          {ejecutando ? 'En ejecución…' : 'Ejecutar validación'}
        </Boton>
      </div>

      <Aviso>
        CP-17 comprueba que la URL pública responda (HTTP 200) y que el elemento configurado esté
        presente. No evalúa la calidad global del código del equipo.
      </Aviso>

      {ejecutando && (
        <p role="status" className="validacion-resultado">
          <Pill tono="warn">En ejecución</Pill>
          El workflow de GitHub Actions está verificando la URL; puede tardar uno o dos minutos.
        </p>
      )}

      {error && <Aviso tipo="error">{error}</Aviso>}
      {!datos && !error && <p className="muted">Cargando validaciones…</p>}

      {datos && !ultima && !ejecutando && (
        <p className="muted">Todavía no hay validaciones de este proyecto.</p>
      )}

      {ultima && (
        <>
          <h3>Último resultado</h3>
          <div className="validacion-resultado">
            <Pill tono={ultima.resultado === 'PASS' ? 'ok' : 'bad'}>{ultima.resultado}</Pill>
            <span>{fechaHoraUtc(ultima.ejecutada_en)}</span>
            <span>Duración: {(ultima.duracion_ms / 1000).toFixed(1)} s</span>
            {ultima.captura_url && (
              <a href={ultima.captura_url} target="_blank" rel="noopener noreferrer">Ver captura del fallo</a>
            )}
          </div>
          <p className="small muted">
            Total registrado: {datos.resumen?.PASS ?? 0} PASS · {datos.resumen?.FAIL ?? 0} FAIL.
          </p>
          <Tabla
            columnas={['Fecha', 'Resultado', 'Duración', 'Ejecución de Actions', 'Captura']}
            filas={datos.items.map(v => [
              fechaHoraUtc(v.ejecutada_en),
              <Pill key={v.id} tono={v.resultado === 'PASS' ? 'ok' : 'bad'}>{v.resultado}</Pill>,
              `${(v.duracion_ms / 1000).toFixed(1)} s`,
              String(v.run_id_actions),
              v.captura_url
                ? <a key={`c${v.id}`} href={v.captura_url} target="_blank" rel="noopener noreferrer">Abrir</a>
                : '—',
            ])}
          />
        </>
      )}
    </article>
  )
}

/** Cifras del Resumen leídas de la API (los datos de ejemplo solo valen para la demostración). */
function ResumenApi({ proyecto }) {
  const commits = useConsulta(obtenerCommits, proyecto.id).datos
  const tareas = useConsulta(obtenerTareas, proyecto.id).datos
  const documentos = useConsulta(obtenerDocumentos, proyecto.id).datos
  const valor = (dato, f) => (dato ? f(dato) : '…')
  return (
    <div className="grid cuatro">
      <Estadistica etiqueta="Commits guardados" valor={valor(commits, d => d.total)} />
      <Estadistica
        etiqueta="Tareas terminadas"
        valor={valor(tareas, d => (d.estado === 'ok' ? `${d.resumen.listo} / ${d.total}` : '—'))}
      />
      <Estadistica etiqueta="Documentos guardados" valor={valor(documentos, d => d.total)} />
      <Estadistica etiqueta="Fuentes previstas" valor="3" />
    </div>
  )
}

export default function Detalle({ proyecto, notionFallo, onNotionFallo, onVolver, onDashboard, pestanaInicial = 'resumen' }) {
  const [pestana, setPestana] = useState(pestanaInicial)

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
          {API_ACTIVA ? (
            <ResumenApi proyecto={proyecto} />
          ) : (
            <div className="grid cuatro">
              <Estadistica etiqueta="Commits de ejemplo" valor="20" />
              <Estadistica etiqueta="Tareas terminadas" valor="8 / 20" />
              <Estadistica etiqueta="Documentos de ejemplo" valor="10" />
              <Estadistica etiqueta="Fuentes previstas" valor="3" />
            </div>
          )}

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
                <b>Periodo:</b> {fechaCorta(proyecto.inicio)} a {fechaCorta(proyecto.fin)}
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

      {pestana === 'github' && API_ACTIVA && <CommitsApi proyecto={proyecto} />}

      {pestana === 'github' && !API_ACTIVA && (
        <article className="card">
          <div className="head">
            <div>
              <div className="eyebrow">HU-003 · CP-06</div>
              <h2>Commits de GitHub</h2>
              <p className="muted">Últimos {COMMITS.length} commits del dataset de demostración (TA-017). Fechas en UTC.</p>
            </div>
            <div>
              <Pill tono="ok">{COMMITS.length} de {COMMITS.length} mostrados</Pill>{' '}
              <Pill tono="warn">Integración: datos de demostración (API pendiente)</Pill>
            </div>
          </div>
          {NOTA_DEMO}
          <Tabla
            columnas={['Autor', 'Fecha', 'Mensaje', 'SHA corto']}
            filas={COMMITS.map(c => [c.autor, c.fecha, c.mensaje, <code key={c.sha}>{c.sha}</code>])}
          />
        </article>
      )}

      {pestana === 'notion' && API_ACTIVA && <TareasNotionApi proyecto={proyecto} />}

      {pestana === 'notion' && !API_ACTIVA && (
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

      {pestana === 'drive' && API_ACTIVA && <DocumentosApi proyecto={proyecto} />}

      {pestana === 'drive' && !API_ACTIVA && (
        <article className="card">
          <div className="head">
            <div>
              <div className="eyebrow">HU-005 · CP-04</div>
              <h2>Documentación de Google Drive</h2>
              <p className="muted">{DOCUMENTOS.length} documentos del dataset de demostración (TA-017). Fechas en UTC.</p>
            </div>
            <div>
              <Pill tono="ok">{DOCUMENTOS.length} de {DOCUMENTOS.length} mostrados</Pill>{' '}
              <Pill tono="warn">Integración: datos de demostración (TA-014 pendiente)</Pill>
            </div>
          </div>
          {NOTA_DEMO}
          <Tabla
            columnas={['Nombre', 'Último editor', 'Última modificación', 'Tipo']}
            filas={DOCUMENTOS.map(d => [d.nombre, d.editor, d.modificado, d.tipo])}
          />
        </article>
      )}

      {pestana === 'validacion' && API_ACTIVA && <ValidacionApi proyecto={proyecto} />}

      {pestana === 'validacion' && !API_ACTIVA && (
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
