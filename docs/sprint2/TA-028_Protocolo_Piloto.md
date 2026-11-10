# TA-028 · Protocolo de la prueba piloto

Entregable: protocolo, ficha de observación y encuesta. Los tres documentos completos están a continuación; el mismo texto está en docs/sprint2/TA-028_Protocolo_Piloto.md para poder editarlo y entregarlo al docente.


## 4.1 Resumen del piloto

| Aspecto | Detalle |
|---|---|
| Objetivo | Comprobar con el docente Walter Cueva, usuario real del sistema, que puede supervisar proyectos de software con la aplicación desplegada: ingresar, consultar la evidencia de GitHub, Notion y Drive, entender indicadores y alertas, validar la aplicación del equipo y emitir el reporte del historial. |
| Cuándo | Semana 12, segunda mitad (jueves 19/11 o viernes 20/11/2026; fecha y hora por confirmar con el docente). Antes: TA-025 (despliegue), TA-029 (2 proyectos piloto) y TA-027 (esta ronda de pruebas) deben estar cerradas. |
| Duración | 60 minutos de sesión: 5 de bienvenida y consentimiento, 35 de tareas, 10 de encuesta y 10 de preguntas finales. |
| Quién | Participante: docente Walter Cueva. Moderador: Castro (ejecuta TA-032). Observador: Mondragón (TA-050, notas de usabilidad). Soporte técnico en segundo plano: Chávez (plataforma) y Reyes (núcleo multiagente). |
| Entorno | URL del frontend desplegado (Vercel) y API en Render con base Neon (TA-025), con los 2 proyectos piloto registrados por TA-029. Navegador Edge o Chrome actualizado. |
| Después | TA-051 (Castro) tabula fichas y encuesta; DO-004 (Chávez) redacta el informe del piloto; TA-031/TA-034/TA-026 absorben los defectos. |


## 4.2 Preparación y lista de verificación previa

| # | Verificación (el día anterior y 30 min antes) | Responsable | Hecho |
|---|---|---|---|
| 1 | La URL del frontend abre y la banda dice «Conectado al servidor» | Castro | ☐ |
| 2 | La API responde a /health. Si estuvo inactiva, se «despierta» abriendo la URL 5 min antes (el arranque en frío del plan gratuito puede tardar cerca de 1 min) | Chávez | ☐ |
| 3 | La cuenta del docente existe y el inicio de sesión funciona (la clave se entrega por canal aparte; no se escribe en este documento) | Castro | ☐ |
| 4 | Los 2 proyectos piloto aparecen en «Mis proyectos» con sus 3 fuentes verificadas (TA-029) | Chávez | ☐ |
| 5 | Ya existe al menos un corte guardado de cada proyecto (se ejecutó la supervisión el día anterior) y al menos una validación CP-17 | Reyes / Castro | ☐ |
| 6 | Se ejecutó la regresión CP-API1–5 contra la URL (workflow «E2E contra producción») y está en verde | Castro | ☐ |
| 7 | Se revisó la cuota de Gemini; si está agotada, las alertas usan la plantilla (se avisa al docente) | Reyes | ☐ |
| 8 | Fichas impresas, encuesta impresa o en formulario, cronómetro y copia del consentimiento listos | Castro | ☐ |
| 9 | Hay un plan B: captura previa de cada pantalla en caso de caída del servicio | Mondragón | ☐ |


## 4.3 Guion de la sesión
1. Bienvenida (5 min). Se explica que se evalúa el sistema, no a la persona, que puede detenerse cuando quiera y que sus respuestas se usarán solo para mejorar la herramienta. Se lee y firma el consentimiento (ficha, parte A).
1. Tareas (35 min). El moderador lee cada tarea tal como está escrita, no da pistas y no toca el teclado; el observador anota. Se pide pensar en voz alta. Si el docente se bloquea más de 2 minutos, se registra «con ayuda» y se le orienta.
1. Encuesta (10 min). Cuestionario SUS más las preguntas de utilidad (sección 4.5).
1. Preguntas finales (10 min): qué fue lo más fácil, qué fue lo más confuso, qué cambiaría primero y si usaría el sistema con sus grupos.

| Id | Tarea (lo que se le dice) | PBI | Éxito si… | Tiempo meta* |
|---|---|---|---|---|
| T1 | «Ingrese al sistema con su cuenta.» | HU-001 | Llega a «Mis proyectos» | ≤ 1 min |
| T2 | «Abra el proyecto del Grupo A y revise cuántos commits, tareas y documentos tiene.» | HU-002–005 | Ve los 3 totales en el Resumen | ≤ 2 min |
| T3 | «En la pestaña de GitHub, diga quién hizo el último commit.» | HU-003 | Identifica autor y fecha | ≤ 1 min |
| T4 | «Vaya al Dashboard y ejecute la supervisión de hoy. Dígame cómo va el proyecto.» | HU-006 | Ejecuta, lee I1–I4 y los interpreta | ≤ 3 min |
| T5 | «Abra una alerta y explíqueme por qué se generó.» | HU-007 | Lee la explicación y la evidencia de origen | ≤ 3 min |
| T6 | «Compruebe si la aplicación de este grupo está funcionando.» | HU-008 | Ejecuta la validación y distingue PASS o FAIL | ≤ 3 min* |
| T7 | «Compare el proyecto entre dos fechas e imprima el reporte.» | HU-009 | Compara cortes y abre la vista de impresión | ≤ 4 min |
| T8 | «Repita T4–T5 con el Grupo B y diga cuál de los dos necesita más atención.» | HU-006, HU-007 | Compara ambos con evidencia | ≤ 5 min |
| T9 | «Cierre la sesión.» | HU-001 | Vuelve al inicio de sesión | ≤ 30 s |


* Los tiempos meta son una propuesta inicial de Castro, basada en las acciones mínimas medidas en la prueba U6 de usabilidad y en la duración real de la validación (≈ 12 s si falla, hasta 2 min con GitHub Actions real). Se ajustan con el docente antes de la sesión.


## 4.4 Qué se mide y criterios de éxito

| Medida | Cómo se mide | Criterio propuesto* |
|---|---|---|
| Tasa de éxito sin ayuda | Tareas completadas sin ayuda / 9 | ≥ 80 % (≥ 7 de 9); ninguna tarea imposible de completar |
| Tiempo por tarea | Cronómetro del moderador, de la lectura de la tarea hasta el éxito | Dentro del tiempo meta en ≥ 70 % de las tareas |
| Errores y clics de más | Conteo del observador | Registrar; revisar toda tarea con ≥ 3 errores |
| Usabilidad percibida | Puntaje SUS (0–100) | ≥ 68 (por encima del promedio) |
| Utilidad percibida | 6 afirmaciones en escala 1–5 | Promedio ≥ 4 y ninguna < 3 |
| Fiabilidad técnica | Caídas, errores 5xx y esperas > 60 s | 0 caídas; cualquier espera se anota con su causa |


* Los criterios son propuestos a partir del guion de usabilidad del Sprint 2 (éxito ≥ 90 %, SUS ≥ 68). El Charter no los fija; se confirman con el docente en la reunión semanal.


## 4.5 Instrumentos

### Ficha de observación (una por tarea)

| Campo | Registro |
|---|---|
| Sesión | Fecha / hora: ______   Proyecto(s): ______   Versión (commit): ______   Navegador: ______ |
| Moderador / Observador | ______ / ______ |
| Tarea (T1–T9) | ______ |
| Hora de inicio / fin | ______ / ______   Tiempo: ____ s |
| ¿Completó? | ☐ Sí, sin ayuda   ☐ Con ayuda   ☐ No |
| Errores o clics de más | ______ |
| Comentarios literales del docente | ______ |
| Incidente técnico (caída, lentitud, mensaje de error) | ______ |
| Severidad del problema | ☐ 0 ninguno  ☐ 1 cosmético  ☐ 2 menor  ☐ 3 mayor  ☐ 4 impide terminar |


### Ficha de consentimiento y cierre (firmada)

| Parte A · Consentimiento |  |
|---|---|
| Texto | He sido informado/a de que se evalúa el sistema y no mi desempeño; que mi participación es voluntaria y puedo detenerla en cualquier momento; que las notas, tiempos y respuestas se usarán solo para mejorar la herramienta y para el informe del curso; y que los datos de los estudiantes que aparezcan se mostrarán con fines de supervisión y no se difundirán fuera de la sesión. |
| Participante | Nombre: ______________________   Cargo: Docente   Firma: ____________   Fecha: ______ |
| Moderador | Nombre: ______________________   Firma: ____________ |
| Parte B · Cierre | Hora de inicio ______   Hora de fin ______   Duración ______ min<br>Tareas sin ayuda: ____ / 9   Incidentes técnicos: ____   Observaciones generales: __________ |


### Encuesta

Parte 1 · Escala de usabilidad (SUS). Marque de 1 (totalmente en desacuerdo) a 5 (totalmente de acuerdo).


| # | Afirmación | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | Creo que me gustaría usar este sistema con frecuencia. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Encontré el sistema innecesariamente complejo. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Pensé que el sistema era fácil de usar. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Creo que necesitaría ayuda de una persona técnica para usarlo. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Encontré que las funciones estaban bien integradas. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Pensé que había demasiada inconsistencia en el sistema. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Imagino que la mayoría de personas aprendería a usarlo muy rápido. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Encontré el sistema muy incómodo de usar. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Me sentí muy seguro/a usando el sistema. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Necesité aprender muchas cosas antes de poder usarlo. | ☐ | ☐ | ☐ | ☐ | ☐ |


Cálculo: en los ítems impares restar 1 a la respuesta; en los pares, restar la respuesta a 5; sumar los diez valores y multiplicar por 2,5 (0 a 100).


Parte 2 · Utilidad para la supervisión. Escala de 1 a 5.


| # | Afirmación | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| U1 | Los indicadores I1–I4 se entienden sin explicación adicional. | ☐ | ☐ | ☐ | ☐ | ☐ |
| U2 | La explicación de cada alerta me permite saber qué revisar. | ☐ | ☐ | ☐ | ☐ | ☐ |
| U3 | La evidencia de origen (commit, tarea o documento) me da confianza en la alerta. | ☐ | ☐ | ☐ | ☐ | ☐ |
| U4 | Este sistema me ahorraría tiempo frente a revisar GitHub, Notion y Drive por separado. | ☐ | ☐ | ☐ | ☐ | ☐ |
| U5 | El resultado de la validación (PASS/FAIL) me resulta claro y útil. | ☐ | ☐ | ☐ | ☐ | ☐ |
| U6 | El reporte imprimible del historial me sirve para mis registros. | ☐ | ☐ | ☐ | ☐ | ☐ |


Parte 3 · Preguntas abiertas.

1. ¿Qué fue lo más fácil de hacer?
1. ¿Qué fue lo más confuso? ¿Hubo un momento en que no supo qué hacer?
1. ¿Qué cambiaría primero?
1. ¿Qué información le faltó para decidir si un grupo necesita atención?
1. ¿Usaría este sistema con sus grupos el próximo ciclo? ¿Por qué?

### Encuesta marcada (ejemplo de llenado)

Ejemplo ilustrativo para mostrar cómo se marca la encuesta y cómo se calcula el puntaje. NO son resultados del piloto: la sesión con el docente todavía no se ha realizado y estas respuestas no pertenecen a ninguna persona real.


| # | Afirmación | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 | Creo que me gustaría usar este sistema con frecuencia. | ☐ | ☐ | ☐ | ☒ | ☐ |
| 2 | Encontré el sistema innecesariamente complejo. | ☐ | ☒ | ☐ | ☐ | ☐ |
| 3 | Pensé que el sistema era fácil de usar. | ☐ | ☐ | ☐ | ☒ | ☐ |
| 4 | Creo que necesitaría ayuda de una persona técnica para usarlo. | ☐ | ☒ | ☐ | ☐ | ☐ |
| 5 | Encontré que las funciones estaban bien integradas. | ☐ | ☐ | ☐ | ☒ | ☐ |
| 6 | Pensé que había demasiada inconsistencia en el sistema. | ☐ | ☒ | ☐ | ☐ | ☐ |
| 7 | Imagino que la mayoría de personas aprendería a usarlo muy rápido. | ☐ | ☐ | ☐ | ☒ | ☐ |
| 8 | Encontré el sistema muy incómodo de usar. | ☐ | ☒ | ☐ | ☐ | ☐ |
| 9 | Me sentí muy seguro/a usando el sistema. | ☐ | ☐ | ☐ | ☒ | ☐ |
| 10 | Necesité aprender muchas cosas antes de poder usarlo. | ☐ | ☒ | ☐ | ☐ | ☐ |


| Ítem | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Suma | ×2,5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Respuesta | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 | 4 | 2 |  |  |
| Aporte | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 30 | 75 |


Puntaje SUS del ejemplo: 30 × 2,5 = 75 (≥ 68: por encima del promedio).


| # | Afirmación | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| U1 | Los indicadores I1–I4 se entienden sin explicación adicional. | ☐ | ☐ | ☐ | ☒ | ☐ |
| U2 | La explicación de cada alerta me permite saber qué revisar. | ☐ | ☐ | ☐ | ☐ | ☒ |
| U3 | La evidencia de origen (commit, tarea o documento) me da confianza en la alerta. | ☐ | ☐ | ☐ | ☒ | ☐ |
| U4 | Este sistema me ahorraría tiempo frente a revisar GitHub, Notion y Drive por separado. | ☐ | ☐ | ☐ | ☐ | ☒ |
| U5 | El resultado de la validación (PASS/FAIL) me resulta claro y útil. | ☐ | ☐ | ☐ | ☒ | ☐ |
| U6 | El reporte imprimible del historial me sirve para mis registros. | ☐ | ☐ | ☒ | ☐ | ☐ |


Promedio de utilidad del ejemplo: 4.2 (criterio: ≥ 4 y ninguna < 3).


## 4.6 Plan de contingencia

| Situación | Qué se hace |
|---|---|
| El servicio gratuito tarda en responder (arranque en frío) | Se abrió la URL 5 min antes; si aún tarda, se explica la espera y se anota el tiempo. Máximo de espera: 2 min. |
| La API no responde o la base cae | Se pasa al plan B: capturas previas de las pantallas y, si es posible, ejecución local del equipo; se registra como incidente de severidad 4. |
| Gemini devuelve 429 | Las alertas usan la plantilla (origen «plantilla»); se explica al docente. No es un fallo. |
| Una fuente (GitHub, Notion o Drive) falla | El Dashboard muestra la fuente en fallo y sigue con las demás: es el comportamiento esperado. Se anota como observación. |
| La validación CP-17 tarda o da FAIL | Esperado: un FAIL tarda ≈ 12 s y una validación con Actions real hasta 2 min. Se pide al docente interpretar el resultado. |
| El docente se bloquea > 2 min | Se marca «con ayuda» y se orienta con una pista mínima; la tarea sigue contando como no resuelta sin ayuda. |
| Aparece un dato personal inesperado | No se difunde; se anota solo el identificador de la evidencia, nunca el nombre. |


## 4.7 Datos y privacidad
- Las fichas firmadas se guardan en el espacio privado del grupo; no se suben al repositorio.
- En el informe del piloto (DO-004) los estudiantes se identifican solo por proyecto; no se incluyen nombres reales.
- Ninguna clave, token ni contraseña se escribe en fichas, capturas ni notas (regla RN-001); la cuenta del docente se entrega aparte.
- Si se graba la pantalla, solo se hace con permiso expreso del docente.

## 4.8 Registro de resultados y cierre
- El mismo día, el moderador transcribe las fichas a una hoja de cálculo con una fila por docente-tarea (insumo de TA-051).
- Los problemas se clasifican por severidad y se abren como issues: los de severidad 3–4 entran a TA-031 (usabilidad), TA-034 (módulo evidencias) o TA-026 (núcleo) según corresponda.
- El informe del piloto (DO-004, Chávez) cita la hoja tabulada; si no alcanza en la semana 12, se termina en la semana 13 (reserva).
