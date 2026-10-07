# Agentes inteligentes para el seguimiento y supervisión de proyectos de software académicos

Taller Integrador 1 · Grupo 12 · UPAO. Aplicación web para el docente: agentes que extraen la evidencia de GitHub, Notion y Google Drive, calculan los indicadores I1–I4 y generan alertas R1–R4.

## Estructura

```
backend/              API FastAPI (Python 3.12), modelos SQLAlchemy y migraciones Alembic
frontend/             React + Vite
tests/                Pruebas con pytest
docs/                 Documentación (modelo de datos y diagrama ER)
.github/workflows/    Workflows de GitHub Actions
.env.example          Nombres de las variables de entorno (sin valores)
```

## Requisitos

- Git
- Python 3.12
- Node.js 20.19 o superior (o 22.12 o superior) y npm
- Una base PostgreSQL 16: la de Neon (plan Free) o una local

## Puesta en marcha

### 1. Clonar y crear el `.env`

```bash
git clone <URL-del-repositorio>
cd <carpeta-del-repositorio>
```

Copia `.env.example` como `.env` (en la raíz) y completa `DATABASE_URL` con la cadena de conexión de tu base. El resto de variables se completan cuando cada tarea las necesite. **`.env` está en `.gitignore`: nunca lo subas.**

### 2. Backend

```bash
cd backend
python -m venv .venv
```

Activa el entorno virtual:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- macOS / Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Comprobación: abre <http://localhost:8000/health> y debe responder `{"status":"ok"}`. La documentación interactiva está en <http://localhost:8000/docs>.

### 3. Base de datos (migraciones)

Con el entorno virtual activo y `DATABASE_URL` en el `.env`:

```bash
cd backend
alembic upgrade head
```

Crea las 8 tablas del sistema (más la tabla de control `alembic_version`). Detalle en [docs/modelo-de-datos.md](docs/modelo-de-datos.md).

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Comprobación: abre <http://localhost:5173>; debe verse la página base sin errores en la consola del navegador.

### 5. Pruebas

Desde la raíz del repositorio, con el entorno virtual del backend activo:

```bash
pytest
```

## Convenciones

- Los secretos (tokens, claves, credenciales) viven solo en `.env` local y en los *Repository secrets* de GitHub. Nunca se hacen commit.
- Un commit por PBI, con su ID en el mensaje. Ejemplo: `TA-004: modelo de datos y migración inicial`.

## Entregables TA-003, TA-035 y RN-001

- [TA-003: plan CP-01 a CP-08 y plantilla de horas](docs/sprint1/TA-003.md).
- [TA-035: integración continua y verificación](docs/sprint1/TA-035.md).
- [RN-001: reglas de seguridad y evidencias](docs/sprint1/RN-001.md).
