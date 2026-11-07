# Pruebas de carga y disponibilidad

Cubren los atributos de calidad de **rendimiento** y **disponibilidad** con [Locust](https://locust.io/) sobre los endpoints que expone Swagger (`/docs`).

## Qué mide

| Escenario | Endpoints | Criterio |
|---|---|---|
| Visitante anónimo | `GET /health`, `GET /auth/me` sin token | `/health` 200; `/auth/me` debe dar 401, nunca 5xx |
| Docente en sesión | `POST /auth/login`, `GET /proyectos`, `GET /proyectos/{id}`, `GET /proyectos/{id}/tareas`, `GET /auth/me` | 2xx sin errores |

La prueba falla (código de salida 1) si los fallos superan `CARGA_MAX_FALLOS_PCT` (1 % por defecto) o el p95 supera `CARGA_P95_MS` (1500 ms por defecto).

## Ejecución local

Con el backend arriba (`uvicorn app.main:app`) y un docente de prueba existente en la base:

```bash
pip install -r pruebas_carga/requirements.txt
export CARGA_CORREO=docente@ejemplo.com CARGA_PASSWORD=...   # PowerShell: $env:CARGA_CORREO=...
locust -f pruebas_carga/locustfile.py --host http://localhost:8000
```

Abre <http://localhost:8089>, pon 50, 100 y 200 usuarios (spawn rate 10) y guarda las capturas como evidencia.

Sin interfaz:

```bash
locust -f pruebas_carga/locustfile.py --headless --host http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 2m --csv pruebas_carga/resultados/carga
```

Sin `CARGA_CORREO`/`CARGA_PASSWORD` solo se ejercita el escenario anónimo.

## En CI

Workflow manual `.github/workflows/carga.yml` (Actions → *Pruebas de carga y disponibilidad*). Pide la URL de la API desplegada y los usuarios (50/100/200). Requiere los *Repository secrets* `CARGA_CORREO` y `CARGA_PASSWORD`. Sube el informe HTML y los CSV como artefacto.

## Resultados documentados

Informe con capturas y conclusiones de las corridas de 50, 100 y 200 usuarios: [docs/carga/pruebas-de-carga.md](../docs/carga/pruebas-de-carga.md). Para ensayar sin PostgreSQL existe `arrancar_local_sqlite.py`.

## Notas

- Prueba contra un entorno de pruebas, no contra producción: `POST /auth/login` y las rutas de tareas consultan la base y Notion.
- `POST /validaciones` queda fuera a propósito: dispara GitHub Actions y consumiría cuota real.
- Las credenciales nunca se escriben en el repositorio.
