# TA-003 · Evidencia de ejecución del plan de pruebas

Reporte generado automáticamente por `scripts/ejecutar_pruebas.py`.
Los resultados son los que devolvió la ejecución real, incluidos los fallos.

## Entorno

| Dato | Valor |
|---|---|
| Fecha de ejecución | 02/10/2026 07:00 UTC |
| Python | 3.11.9 |
| Autenticado en GitHub | sí |
| Repositorio de prueba | octocat/Hello-World |
| Peticiones restantes | 5000/5000 |

## Resumen

- ✅ Aprobados: **5**
- ❌ Fallidos: **0**
- ⏸️ Bloqueados (sin implementación aún): **5**
- Total de casos: **10**

## Resultados

| Caso | PBI | Resultado | Obtenido |
|---|---|---|---|
| **CP-01** Conexión con GitHub y lectura de actividad | HU-001 | ✅ APROBADO | 3 commits, 1000 PR, 756 issues, 3 rama(s) |
| **CP-02a** Repositorio inexistente (404) | HU-001 | ✅ APROBADO | HTTP 404 al consultar https://api.github.com/repos/octocat/no-existe-xyz-123/commits?per_page=100 |
| **CP-02b** Host inalcanzable / caída de red | HU-001 | ✅ APROBADO | Error de red al consultar https://api.github.invalido/rate_limit: [Errno 11001] getaddrinfo failed |
| **CP-02c** Conservar última sincronización al fallar | HU-001 | ✅ APROBADO | commits conservados=True (3), estado_fuente='degradada' |
| **CP-06** Cálculo de indicadores (Gini, ritmo, autores) | HU-005 | ✅ APROBADO | 8/8 correctas |
| **CP-03** Integración del gestor de tareas (Notion) | HU-002 | ⏸️ BLOQUEADO | No ejecutable: el agente de Notion aún no está implementado (HU-002 en curso). |
| **CP-04** Integración de documentación (Google Drive) | HU-003 | ⏸️ BLOQUEADO | No ejecutable: el agente de Drive aún no está implementado (HU-003 pendiente). |
| **CP-05** Consolidación por equipo y semana (3 fuentes) | HU-004 | ⏸️ BLOQUEADO | No ejecutable parcialmente: solo existe la fuente GitHub; faltan Notion y Drive. |
| **CP-07** Detección de retrasos y semáforo de riesgo | HU-006 | ⏸️ BLOQUEADO | No ejecutable: la clasificación de riesgo solo existe como maqueta en el prototipo. |
| **CP-08** Acceso por roles y aislamiento de datos | RN-001 | ⏸️ BLOQUEADO | No automatizable aún: el control de roles solo existe en el prototipo HTML. Verificado de forma visual (ver evidencia... |

## Detalle por caso

### ✅ CP-01 · Conexión con GitHub y lectura de actividad

- **PBI:** HU-001
- **Resultado esperado:** Lista commits/PRs/issues con autor y fecha
- **Obtenido:** 3 commits, 1000 PR, 756 issues, 3 rama(s)

```
Repositorio: octocat/Hello-World
Muestra de commits:
[
  {
    "sha": "7fd1a60",
    "mensaje": "Merge pull request #6 from Spaceghost/patch-1",
    "autor": "octocat",
    "fecha": "2012-03-06T23:06:50Z"
  },
  {
    "sha": "7629413",
    "mensaje": "New line at end of file. --Signed off by Spaceghost",
    "autor": "Spaceghost",
    "fecha": "2011-09-14T04:42:41Z"
  }
]
```

### ✅ CP-02a · Repositorio inexistente (404)

- **PBI:** HU-001
- **Resultado esperado:** Error controlado (GitHubError), el agente sigue vivo
- **Obtenido:** HTTP 404 al consultar https://api.github.com/repos/octocat/no-existe-xyz-123/commits?per_page=100

```
Traceback (most recent call last):
  File "C:\Users\COMPUTER\Downloads\ProyectoAgente\scripts\github_client.py", line 102, in _get
    with urllib.request.urlopen(peticion, timeout=self.timeout) as resp:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\COMPUTER\AppData\Local\Programs\Python\Python311\Lib\urllib\request.py", line 216, in urlopen
    return opener.op
```

### ✅ CP-02b · Host inalcanzable / caída de red

- **PBI:** HU-001
- **Resultado esperado:** Error controlado (GitHubError)
- **Obtenido:** Error de red al consultar https://api.github.invalido/rate_limit: [Errno 11001] getaddrinfo failed

```
Traceback (most recent call last):
  File "C:\Users\COMPUTER\AppData\Local\Programs\Python\Python311\Lib\urllib\request.py", line 1348, in do_open
    h.request(req.get_method(), req.selector, req.data, headers,
  File "C:\Users\COMPUTER\AppData\Local\Programs\Python\Python311\Lib\http\client.py", line 1303, in request
    self._send_request(method, url, body, headers, encode_chunked)
socket.gaie
```

### ✅ CP-02c · Conservar última sincronización al fallar

- **PBI:** HU-001
- **Resultado esperado:** Mantiene los datos previos y marca estado_fuente='degradada'
- **Obtenido:** commits conservados=True (3), estado_fuente='degradada'

```
[recolector] Prueba Degradacion: 3 commits, 1000 PR, 756 issues

[recolector] ⚠ Prueba Degradacion: HTTP 404 al consultar https://api.github.com/repos/octocat/no-existe-xyz-123/commits?per_page=100 Se conserva la última sincronización.
```

### ✅ CP-06 · Cálculo de indicadores (Gini, ritmo, autores)

- **PBI:** HU-005
- **Resultado esperado:** 8 aserciones correctas
- **Obtenido:** 8/8 correctas

```
OK   Gini reparto equitativo [5,5,5,5]: obtenido=0.0 esperado=0.0
OK   Gini una sola persona [20,0,0,0]: obtenido=0.75 esperado=0.75
OK   Gini normalizado [20,0,0,0]: obtenido=1.0 esperado=1.0
OK   Gini caso Beta [74,14,9,3]: obtenido=0.545 esperado=0.545
OK   Gini normalizado caso Beta: obtenido=0.727 esperado=0.727
OK   Días con commit (2 fechas distintas): obtenido=2 esperado=2
OK   Integrantes detectados: obtenido=2 esperado=2
OK   Commits totales: obtenido=3 esperado=3
```

### ⏸️ CP-03 · Integración del gestor de tareas (Notion)

- **PBI:** HU-002
- **Resultado esperado:** Lee tareas con responsable, estado y fecha; marca las incompletas
- **Obtenido:** No ejecutable: el agente de Notion aún no está implementado (HU-002 en curso).

### ⏸️ CP-04 · Integración de documentación (Google Drive)

- **PBI:** HU-003
- **Resultado esperado:** Lista documentos con fecha y marca entregables faltantes
- **Obtenido:** No ejecutable: el agente de Drive aún no está implementado (HU-003 pendiente).

### ⏸️ CP-05 · Consolidación por equipo y semana (3 fuentes)

- **PBI:** HU-004
- **Resultado esperado:** Unifica GitHub + Notion + Drive por equipo y semana
- **Obtenido:** No ejecutable parcialmente: solo existe la fuente GitHub; faltan Notion y Drive.

### ⏸️ CP-07 · Detección de retrasos y semáforo de riesgo

- **PBI:** HU-006
- **Resultado esperado:** Clasifica verde/amarillo/rojo con causa y evidencia
- **Obtenido:** No ejecutable: la clasificación de riesgo solo existe como maqueta en el prototipo.

### ⏸️ CP-08 · Acceso por roles y aislamiento de datos

- **PBI:** RN-001
- **Resultado esperado:** Login por rol; el estudiante solo ve su equipo
- **Obtenido:** No automatizable aún: el control de roles solo existe en el prototipo HTML. Verificado de forma visual (ver evidencias/prototipo/11_estudiante.png).

## Interpretación

Los casos **CP-01**, **CP-02a/b/c** y **CP-06** se ejecutan contra la
implementación real (`scripts/github_client.py` y `scripts/sync_github.py`)
y cubren el criterio de HU-001: *si la API falla o excede su límite, el
sistema sigue funcionando*.

Los casos **CP-03, CP-04, CP-05 y CP-07** quedan **bloqueados** porque
sus agentes (Notion, Drive, análisis de riesgo) todavía no están
implementados; se dejan registrados para ejecutarlos al cerrar esas
historias. **CP-08** solo puede verificarse de forma visual mientras el
control de roles viva únicamente en el prototipo.

> Este reporte no maquilla resultados: un caso bloqueado significa que la
> funcionalidad aún no existe, no que la prueba haya pasado.
