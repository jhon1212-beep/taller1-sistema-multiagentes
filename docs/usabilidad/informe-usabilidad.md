# Pruebas de usabilidad del frontend

Responsable: Mondragón. Fecha de ejecución: 3 de noviembre de 2026. Informe completo con capturas: [Pruebas_de_Usabilidad_Mondragon.docx](Pruebas_de_Usabilidad_Mondragon.docx).

Alcance: las 8 pantallas del frontend (prototipo con datos simulados), probadas en escritorio (1366 px), tableta (768 px) y móvil (375 px) con Playwright sobre Edge. **No incluye pruebas con personas reales**: el procedimiento está en [guion-usuarios.md](guion-usuarios.md) y sus resultados están pendientes.

## Resultados

Ejecución completa: 10 casos, 6 aprobados y 4 con hallazgos (los hallazgos hacen fallar la prueba a propósito).

| Prueba | Resultado | Resumen |
|---|---|---|
| U1 Capturas | Aprobada | 24 capturas (8 pantallas × 3 dispositivos) |
| U2 Accesibilidad (axe-core) | Hallazgos | Contraste insuficiente en las 8 pantallas; barra de progreso sin nombre en el Dashboard |
| U3 Teclado | Aprobada | Orden lógico, foco visible, Enter envía el formulario |
| U4 Responsive | Hallazgo | Desborda 21 px a 320 px en el Detalle; sin problemas a 375 px ni con zoom 200 % |
| U5 Objetivos táctiles | Hallazgo | 2 enlaces del Detalle de 22 px de alto (mínimo 24 px) |
| U6 Tareas | Aprobada | 6 de 6 tareas completadas, con el mínimo de acciones |
| U7 Errores del formulario | Aprobada | 3 de 3 casos muestran mensaje; solo se informa de un error a la vez |
| U8 Metadatos | Hallazgo | Mismo título de documento en las 8 pantallas; el login no tiene `<main>` |

Lighthouse (solo login): accesibilidad 95 / 100, buenas prácticas 96 / 100, SEO 82 / 82 (escritorio / móvil).

## Hallazgos priorizados

| Id | Hallazgo | Sev. | Corrección propuesta |
|---|---|---|---|
| H1 | Contraste de `.eyebrow` (4,48:1) y del texto secundario (4,33:1) menor a 4,5:1 | 3 | Oscurecer `--brand2` y `--muted` en `tokens.css` |
| H2 | `role="progressbar"` sin nombre accesible | 3 | `aria-label` en el componente `Barra` |
| H3 | Formulario: un solo error por envío y campo sin señalar | 3 | Validar todo a la vez, `aria-invalid` y enfocar el primer error |
| H4 | Título del documento igual en todas las vistas | 2 | Actualizar `document.title` por ruta |
| H5 | Desbordamiento a 320 px en el Detalle | 2 | `overflow-wrap: anywhere` en los enlaces de fuentes |
| H6 | Enlaces de 22 px de alto | 2 | Aumentar el relleno vertical |
| H7 | Botón «Mis proyectos» duplicado y etiquetas de volver inconsistentes | 2 | Unificar el nombre |
| H8 | «Desactivar» sin confirmación | 2 | Confirmar o permitir deshacer |
| H9 | Menú móvil sin plegar (≈ 280 px antes del contenido) | 2 | Menú hamburguesa en pantallas pequeñas |
| H10 | Login sin `<main>`; sin meta description | 1 | Añadirlos |
| H11 | Código interno «HU-001» visible en el login | 1 | Quitarlo del texto |

No se modificó el código del frontend; son recomendaciones.

## Limitaciones

Pruebas automáticas y revisión experta (no sustituyen a las personas); un solo navegador (Edge); Lighthouse solo cubre el login porque requiere sesión para el resto; no se probaron lectores de pantalla reales.

## Evidencias

- `capturas/`: 24 capturas de pantallas completas más las de errores y desbordamiento.
- `evidencias/`: montajes por dispositivo, consola de Playwright, informes de Lighthouse en imagen y recortes.
- `resultados/`: medidas en JSON (axe, teclado, responsive, objetivos táctiles, tareas, errores, metadatos).
- `lighthouse/`: informes HTML y JSON.
