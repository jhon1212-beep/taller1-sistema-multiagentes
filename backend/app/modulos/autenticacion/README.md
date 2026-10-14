# Módulo autenticacion

Dueño: Castro. Contrato publicado en AR-04 (ver `docs/sprint1/AR-04.md`).

| Archivo | Contenido |
|---|---|
| `dominio.py` | `Docente`, `Sesion`, `CredencialesInvalidas`, `SesionInvalida` |
| `puertos.py` | Protocol `ServicioAutenticacion` (`iniciar_sesion`, `obtener_docente`, `cerrar_sesion`) |
| `adaptadores/falso.py` | `ServicioAutenticacionFalso`: en memoria, con los 5 docentes demo del frontend |

Pendiente (fuera de AR-04): adaptador real con bcrypt y la tabla `docente`, y
las rutas HTTP de login.
