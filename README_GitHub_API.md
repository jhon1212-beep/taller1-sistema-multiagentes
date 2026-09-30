# EN-001 · Configuración de la GitHub API

Integración real de solo lectura con la GitHub API para el agente recolector (HU-001).
Sin dependencias externas: usa solo la librería estándar de Python 3.11+.

## Estructura

```
ProyectoAgente/
├── .env                      ← TU token (no se versiona)
├── .env.example              ← plantilla sin credenciales
├── config/
│   ├── equipos.json          ← mapeo equipo → repositorio
│   └── equipos.ejemplo.json  ← repos públicos, para probar sin token
├── scripts/
│   ├── github_client.py      ← cliente de la API (commits, ramas, PRs, issues)
│   ├── sync_github.py        ← agente recolector + indicadores
│   └── test_indicadores.py   ← pruebas (CP-01 / CP-02)
└── data/                     ← salida JSON (no se versiona)
```

## Paso 1 · Crear el token (lo haces tú, en GitHub)

1. GitHub → **Settings → Developer settings → Fine-grained tokens → Generate new token**
2. **Resource owner:** la organización del curso
3. **Repository access:** *Only select repositories* → los repos de los equipos
4. **Permissions**, todos en **Read-only**:

| Permiso | Para qué |
|---|---|
| Contents | Leer commits y ramas |
| Pull requests | Leer PRs y su estado |
| Issues | Leer issues y etiquetas |
| Metadata | Obligatorio |

> Nunca se piden permisos de escritura.

## Paso 2 · Crear el archivo `.env`

Copia `.env.example` a `.env` y pega tu token:

```
GITHUB_TOKEN=github_pat_tu_token_real
GITHUB_ORG=curso-ingsoft-2026-II
GITHUB_API_URL=https://api.github.com
```

`.env` ya está en `.gitignore`. **Nunca lo subas al repositorio.**

## Paso 3 · Registrar los repositorios

Edita `config/equipos.json` con los repos reales de cada equipo:

```json
{ "nombre": "Equipo Beta", "repositorio": "beta-reservas",
  "deadline_sprint": "2026-10-16T23:59:00Z" }
```

Si el repo está en otra cuenta, escribe `owner/repo`.

## Paso 4 · Usar

```bash
# Probar la conexión y ver el límite de peticiones
python scripts/sync_github.py --check

# Sincronizar todos los equipos
python scripts/sync_github.py

# Un solo equipo
python scripts/sync_github.py --equipo Beta

# Prueba de humo sin token (repositorio público)
python scripts/sync_github.py --config equipos.ejemplo.json

# Pruebas de los indicadores
python scripts/test_indicadores.py
```

## Salida

- `data/github_<equipo>.json` — commits, ramas, PRs e issues con **autor y fecha**
- `data/resumen_github.json` — resumen consolidado + indicadores por equipo

Indicadores calculados por equipo:

| Indicador | Campo |
|---|---|
| Commits totales / en ventana | `commits_total`, `commits_en_ventana` |
| Distribución por integrante | `commits_por_autor` |
| Ritmo y regularidad | `dias_con_commit` de `dias_ventana` |
| Concentración antes del deadline | `pct_commits_48h_previas` |
| Equidad contributiva | `gini`, `gini_normalizado` |

> **Sobre el Gini normalizado:** para *n* integrantes el máximo alcanzable es
> (n−1)/n, no 1. Un equipo de 3 nunca pasaría de 0.667. Por eso se normaliza:
> así los equipos de distinto tamaño se comparan de forma justa.

## Límites y fallos (criterio de HU-001)

- Autenticado: **5000 peticiones/hora**. Anónimo: 60/hora y solo repos públicos.
- Antes de cada corrida se consulta `GET /rate_limit`.
- Si la API responde **403/429** (límite) o falla la red, el agente:
  1. conserva los datos de la última sincronización,
  2. marca la fuente como `"estado_fuente": "degradada"`,
  3. registra la incidencia en `resumen_github.json` con el tiempo de reintento.

El sistema **sigue funcionando** en ese caso, que es justamente lo que pide el
criterio de aceptación de HU-001 y lo que verifica el caso de prueba CP-02.

## Estado de verificación

| Prueba | Resultado |
|---|---|
| Conexión real a `api.github.com` | ✔ OK |
| Lectura de commits/PRs/issues (repo público) | ✔ OK |
| Cálculo de Gini y ritmo | ✔ 10/10 pruebas |
| Repositorio inexistente (404) | ✔ error controlado |
| Host inalcanzable | ✔ error controlado |
| Token real | ⏳ pendiente: requiere tu token |
