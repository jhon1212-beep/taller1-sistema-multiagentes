# TA-029 · Registrar los 2 proyectos piloto y verificar sus fuentes

**Responsable (R):** Chávez · **Semana:** 11 (atrasada a la 12) · **Antes de:** TA-032 (piloto, 19 o 20/11)
**Evidencia esperada:** autorizaciones + capturas + verificaciones.

## 1. Pasos

| # | Paso | Evidencia | Hecho |
|---|---|---|---|
| 1 | Elegir 2 grupos del curso con repositorio en GitHub y tareas en Notion (Drive es opcional) | Nombres de los grupos en el acta de la daily | ☐ |
| 2 | Pedir la autorización escrita de cada grupo (texto de la sección 2), por correo o mensaje | Captura o PDF de cada respuesta en el espacio privado del grupo (no en el repo si tiene correos personales) | ☐ |
| 3 | Pedir los accesos según `docs/sprint2/Conectar_fuentes_de_otro_equipo.md` | — | ☐ |
| 4 | Verificar las fuentes con los adaptadores reales | `python backend/scripts/ta029_verificar_fuentes.py --proyecto "Grupo A" --github <url> --notion <url> [--drive <url>]` → `docs/sprint2/evidencias/TA-029_Grupo_A.json` (salida 0 = listo) | ☐ |
| 5 | Registrar cada proyecto en la aplicación desplegada (formulario «Registrar proyecto») con la cuenta del docente del piloto | Captura de «Mis proyectos» con los 2 proyectos | ☐ |
| 6 | Ejecutar la supervisión una vez por proyecto (Dashboard → Ejecutar supervisión) | Captura del Dashboard de cada uno con «X de Y disponibles» | ☐ |
| 7 | Avisar a Castro y Reyes (checklist 4 y 5 del protocolo TA-028) | Mensaje en el grupo | ☐ |

## 2. Texto de autorización (para enviar a cada grupo)

> Hola, somos el Grupo 8 del Taller Integrador 1. Para la prueba piloto de nuestro sistema
> de supervisión con el docente Walter Cueva (19 o 20/11/2026), les pedimos permiso para
> que el sistema **lea en modo solo lectura** el repositorio de GitHub, la base de tareas
> de Notion y, si la usan, la carpeta de Google Drive de su proyecto «______».
>
> - El sistema no modifica nada en sus herramientas.
> - Los nombres de los integrantes no se envían a servicios de IA (se reemplazan por alias).
> - En el informe del piloto el grupo se identifica solo por el nombre del proyecto.
> - Pueden retirar el permiso cuando quieran; al terminar el curso revocamos los accesos.
>
> Si están de acuerdo, respondan «Autorizamos» con el nombre del proyecto y los enlaces.

## 3. Registro

| Proyecto | Grupo | Autorización (fecha) | GitHub | Notion | Drive | Verificación (JSON) | Registrado |
|---|---|---|---|---|---|---|---|
| Piloto A | | | ☐ ok | ☐ ok | ☐ ok ☐ no usa | | ☐ |
| Piloto B | | | ☐ ok | ☐ ok | ☐ ok ☐ no usa | | ☐ |
