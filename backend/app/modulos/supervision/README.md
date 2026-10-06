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

## Verificación

Desde la raíz del repositorio, en PowerShell:

    .\backend\.venv\Scripts\python.exe -m pytest tests/test_supervision_contrato.py -q --tb=short

## Límites y trabajo posterior

TypedDict describe tipos, pero no valida los datos en ejecución.
Los campos específicos de Notion necesarios para calcular indicadores
y reglas requieren acordarse con el módulo evidencias.

La persistencia PostgreSQL, Gemini y el grafo ejecutable se implementan
en los PBIs posteriores.

Los contratos quedan sujetos a revisión de sus consumidores.