# Guion de prueba de usabilidad con usuarios

Este guion es para aplicarlo con **personas reales** (docentes o compañeros que no hayan usado el prototipo). Las pruebas automáticas de `pruebas_usabilidad/` no lo sustituyen: miden accesibilidad y flujos, pero no cuánto entiende una persona la interfaz.

**Resultado de esta sección: pendiente.** Este documento solo deja listo el procedimiento; no contiene respuestas de usuarios.

## Preparación

- Participantes: 5 personas bastan para detectar la mayoría de problemas de usabilidad (Nielsen).
- Entorno: prototipo en `http://localhost:4173` (o la URL desplegada). Credenciales de demostración que muestra la propia pantalla de inicio.
- Equipo: un moderador que no ayuda ni da pistas, y un observador que anota. Grabar la pantalla si la persona lo autoriza.
- Consentimiento: explicar que se evalúa el sistema, no a la persona, y que puede parar cuando quiera.

## Introducción para el participante

«Eres docente y supervisas proyectos de estudiantes. Te voy a pedir que hagas varias tareas con esta aplicación. Piensa en voz alta y dime qué esperas que pase. No hay respuestas incorrectas.»

## Tareas

Las mismas que se automatizaron en la prueba U6, para poder comparar el tiempo de una persona con el mínimo posible.

| Id | Tarea (lo que se le dice) | Éxito si… | Mínimo de acciones | Tiempo automático |
|---|---|---|---:|---:|
| T1 | «Entra a la aplicación con la cuenta de demostración.» | Llega a Mis proyectos | 3 | < 1 s |
| T2 | «Registra un proyecto nuevo con los datos que te doy.» | Aparece el aviso de proyecto guardado | 12 | < 1 s |
| T3 | «Abre el detalle del primer proyecto y vuelve al listado.» | Vuelve a Mis proyectos | 2 | < 1 s |
| T4 | «Ve al Dashboard y ejecuta una supervisión.» | Aparece la traza de ejecución | 2 | < 1 s |
| T5 | «Abre el detalle de la alerta que aparece.» | Ve la evidencia de la alerta | 1 | < 1 s |
| T6 | «Cierra la sesión.» | Vuelve a la pantalla de inicio de sesión | 1 | < 1 s |

## Qué registrar por tarea

| Participante | Tarea | ¿Completó? (sí / con ayuda / no) | Tiempo | Errores o clics de más | Comentarios literales |
|---|---|---|---|---|---|
| P1 | T1 | | | | |

## Cuestionario SUS (System Usability Scale)

Al terminar, cada participante puntúa de 1 (totalmente en desacuerdo) a 5 (totalmente de acuerdo):

1. Creo que me gustaría usar este sistema con frecuencia.
2. Encontré el sistema innecesariamente complejo.
3. Pensé que el sistema era fácil de usar.
4. Creo que necesitaría ayuda de una persona técnica para usarlo.
5. Encontré que las funciones estaban bien integradas.
6. Pensé que había demasiada inconsistencia en el sistema.
7. Imagino que la mayoría de personas aprendería a usarlo muy rápido.
8. Encontré el sistema muy incómodo de usar.
9. Me sentí muy seguro/a usando el sistema.
10. Necesité aprender muchas cosas antes de poder usarlo.

**Cálculo:** en los ítems impares restar 1 a la respuesta; en los pares, restar la respuesta a 5. Sumar los diez valores y multiplicar por 2,5. Resultado de 0 a 100: **68 o más** se considera por encima del promedio; **80 o más**, muy bueno.

## Preguntas finales

- ¿Qué fue lo más fácil? ¿Y lo más confuso?
- ¿Hubo algún momento en que no supiste qué hacer a continuación?
- ¿Qué cambiarías primero?

## Criterios de aceptación sugeridos

- Tasa de éxito ≥ 90 % por tarea sin ayuda.
- SUS promedio ≥ 68.
- Ningún problema de severidad alta (impide completar una tarea) sin plan de corrección.
