# Conectar las fuentes de cualquier equipo

El sistema no está atado al repositorio, al Notion ni al Drive del Grupo 8. Cada proyecto guarda sus propios enlaces y los agentes los leen por proyecto. Este documento explica qué debe hacer cada equipo para que el sistema pueda leer sus fuentes. Sirve para registrar los proyectos piloto (TA-029).

## Lo que el docente registra en el formulario

Pega los enlaces tal como salen en el navegador. El backend extrae el identificador que necesita cada API (`backend/app/modulos/evidencias/referencias.py`):

| Fuente | Enlace de ejemplo | Lo que usa la API |
|---|---|---|
| GitHub | `https://github.com/org/repo` | `org/repo` |
| Notion | `https://app.notion.com/p/Tareas-<32 caracteres>` o `https://www.notion.so/...` | el id de la base |
| Drive | `https://drive.google.com/drive/folders/<id>?usp=sharing` | el id de la carpeta |

## Lo que el equipo debe permitir

### GitHub
- **Repositorio público:** no hace falta nada más.
- **Repositorio privado:** agregar como colaborador, con permiso de lectura, a la cuenta dueña del `GITHUB_TOKEN` del sistema. También sirve que el repositorio esté en la organización del curso (`GITHUB_ORG`) y que esa cuenta sea miembro.
- Se leen los commits de la rama principal.

### Notion
Una integración interna de Notion solo ve su propio espacio de trabajo. Por eso:
- **Base dentro del espacio del Grupo 8:** basta con conectarle la integración del sistema (menú «…» → Conexiones). Usa `NOTION_TOKEN`.
- **Base en el espacio del propio equipo** (lo normal):
  1. El equipo crea una integración interna en su espacio (Configuración → Conexiones → Desarrollar integraciones), con permiso de solo lectura.
  2. La conecta a su base de tareas (menú «…» → Conexiones).
  3. Entrega el token de la integración por un canal privado.
  4. El token se agrega a `NOTION_TOKENS` en Render y en los secrets de GitHub, por ejemplo `{"<id de su base>": "<su token>"}`. Nunca va en el repositorio.
- **La base no necesita copiar la nuestra.** El agente reconoce las columnas por su tipo:
  - el título de la tarea;
  - una columna de personas (responsable);
  - una columna de estado (tipo *Status* o *Select*);
  - una columna de fecha (fecha límite).
  Si hay varias del mismo tipo, prefiere los nombres habituales: `Responsable`/`Assignee`, `Estado`/`Status` y `Fecha límite`/`Due`.
- **Estados reconocidos:**

  | Estado del sistema | Equivalentes que entiende |
  |---|---|
  | `Listo` | `Done`, `Completado`, `Terminado`, `Hecho`… |
  | `En curso` | `In progress`, `En progreso`, `En revisión`… |
  | `Sin empezar` | `Not started`, `Por hacer`, `To-do`, `Pendiente`… |

  Un estado distinto (por ejemplo `Bloqueado`) se guarda vacío: la tarea cuenta como no terminada y no se pierde el corte.

### Google Drive
- Compartir la carpeta del proyecto, como **Lector**, con el correo de la cuenta de servicio (el `client_email` del JSON del sistema). Que la carpeta sea «cualquiera con el enlace» no basta para la API.
- Se leen los documentos de la carpeta y de sus subcarpetas, hasta 3 niveles y 50 carpetas. También funciona dentro de unidades compartidas.

## Cómo comprobarlo

1. Registrar el proyecto con sus 3 enlaces.
2. Abrir el Detalle del proyecto y revisar las pestañas GitHub, Notion y Google Drive.
3. En el Dashboard, pulsar «Ejecutar supervisión». Las tarjetas de fuentes deben decir «Disponible». Si una dice «Integración fallida», el mensaje indica cuál de los permisos anteriores falta. Las otras fuentes siguen funcionando (RN-002).
