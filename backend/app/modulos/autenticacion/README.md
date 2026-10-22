# Módulo autenticacion

Dueño: Castro. Contrato publicado en AR-04 (ver `docs/sprint1/AR-04.md`);
implementación real en HU-001 (ver `docs/sprint1/HU-001.md`).

| Archivo | Contenido |
|---|---|
| `dominio.py` | `Docente`, `Sesion`, `CredencialesInvalidas`, `SesionInvalida` |
| `puertos.py` | Protocols `ServicioAutenticacion` y `RepositorioDocentes` |
| `servicio.py` | `ServicioAutenticacionReal` (bcrypt + JWT) y `hashear_password` |
| `rutas.py` | `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` y la dependencia `docente_actual` |
| `adaptadores/falso.py` | `ServicioAutenticacionFalso`: en memoria, con los 5 docentes demo del frontend |
| `adaptadores/memoria.py` | `RepositorioDocentesMemoria` (pruebas) |
| `adaptadores/sql.py` | `RepositorioDocentesSQL` sobre la tabla `docente` |

Requiere la variable `JWT_SECRET` (mínimo 32 caracteres). Pendiente: que `proyectos`
use `docente_actual` de este módulo en lugar de su función temporal (Chávez).
