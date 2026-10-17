# Módulo supervision

Responsable: Reyes Guerrero Luis Benjamin.

## Contrato AR-02

Este módulo define el estado compartido del grafo y los contratos para
generar explicaciones y almacenar cortes de supervisión.

## Archivos

- dominio.py: tipos Fuente, EstadoFuente, Indicadores, Alerta y Explicacion.
- grafo/estado.py: EstadoSupervision y crear_estado_inicial.
- puertos.py: GeneradorExplicacion y RepositorioSupervision.
- adaptadores/plantilla.py: explicaciones deterministas sin LLM.
- adaptadores/memoria.py: almacenamiento temporal de cortes.
- grafo/supervisor.py: Agente Supervisor y orquestación paralela de GitHub, Notion y Drive.
- ../../../scripts/run_supervisor.py: script de ejecución y generación del consolidado TA-015.

## Estado inicial

Cada ejecución comienza con evidencias y alertas vacías, fuentes
pendientes e indicadores sin calcular (None).

Se reutiliza Evidencia del contrato AR-01.
Los imports utilizan el paquete app, con backend en la ruta de Python.

## Generador de explicaciones

generar(alerta, fecha_corte) devuelve texto y origen.

La plantilla explica una alerta previamente detectada y menciona
su regla, fuente, fecha de corte e identificadores de evidencia.
Rechaza reglas desconocidas y fuentes incompatibles.

No calcula indicadores ni evalúa si una regla se cumple.
No consulta Gemini ni APIs externas.

## Repositorio de supervisión

- guardar(estado): guarda o reemplaza un corte.
- obtener(proyecto_id, fecha_corte): devuelve el corte o None.
- listar(proyecto_id): devuelve sus cortes en orden cronológico ascendente.

Las fechas deben estar en formato ISO 8601 con zona horaria.
Fechas equivalentes se normalizan a UTC para identificar el mismo corte.

El adaptador en memoria utiliza copias independientes al guardar
y consultar. Sus datos se pierden al finalizar el proceso.

## Agente Supervisor (TA-015)

El Agente Supervisor utiliza LangGraph con un patrón de supervisor
jerárquico para coordinar las fuentes de evidencia del proyecto.

El flujo de ejecución es:

`START -> supervisor -> [github_agent | notion_agent | drive_agent] -> consolidate -> END`

El nodo `supervisor` valida la fecha de corte y determina qué fuentes
pueden consultarse.

Los nodos `github_agent`, `notion_agent` y `drive_agent` reciben únicamente
la referencia correspondiente a su fuente y pueden ejecutarse en paralelo.

Cada agente utiliza el contrato `FuenteEvidencia`, conserva únicamente las
evidencias de su fuente y proyecto, y aplica la fecha de corte indicada.

Las evidencias posteriores al corte se descartan y se contabilizan como
`fuera_de_corte`. Las evidencias sin fecha se conservan.

Si un adaptador genera una excepción, únicamente esa fuente queda en estado
`fallo`; las demás fuentes continúan su ejecución.

Una fuente sin adaptador o sin referencia también queda en estado `fallo`
sin ser invocada.

El nodo `consolidate` reúne las evidencias de las fuentes, elimina duplicados
por `(fuente, id_externo)` y ordena el resultado por fecha descendente.

Al finalizar, ninguna fuente debe permanecer en estado `pendiente`.

TA-015 no utiliza LLM. Los indicadores I1-I4 y las reglas R1-R4 se integrarán
en PBIs posteriores.

El script de ejecución es:

    python backend\scripts\run_supervisor.py

El script genera un consolidado JSON en:

    docs\sprint1\evidencias\TA-015_consolidado.json

## Verificación

Desde la raíz del repositorio, en PowerShell:

    .\backend\.venv\Scripts\python.exe -m pytest tests/unit/test_supervision_contrato.py -q --tb=short

Para ejecutar las pruebas unitarias y de integración por carpetas:

    python -m pytest tests/unit tests/integration -q

## Límites y trabajo posterior

TypedDict describe tipos, pero no valida los datos en ejecución.
Los campos específicos de Notion necesarios para calcular indicadores
y reglas requieren acordarse con el módulo evidencias.

La persistencia PostgreSQL, Gemini y el grafo ejecutable se implementan
en los PBIs posteriores.

Los contratos quedan sujetos a revisión de sus consumidores.