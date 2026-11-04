# Pruebas de usabilidad y accesibilidad

Cubren el atributo de calidad de **usabilidad** del frontend (React + Vite) con [Playwright](https://playwright.dev/) y [axe-core](https://github.com/dequelabs/axe-core).

| Prueba | Qué comprueba |
|---|---|
| U1 | Capturas de las 8 pantallas en escritorio, tableta y móvil |
| U2 | Accesibilidad automática WCAG 2.1 A y AA con axe-core |
| U3 | Navegación por teclado, foco visible y envío con Enter |
| U4 | Responsive: sin scroll horizontal a 375 px, 320 px y con zoom del 200 % |
| U5 | Tamaño mínimo de los objetivos táctiles (24 px, WCAG 2.2 criterio 2.5.8) |
| U6 | Seis tareas del docente: éxito, acciones y tiempo |
| U7 | Mensajes de error del formulario |
| U8 | Idioma, título del documento y encabezados |

Las pruebas que encuentran un problema **fallan a propósito** (`expect.soft`): el fallo es el hallazgo. El detalle y la evidencia están en [docs/usabilidad/](../docs/usabilidad/).

## Ejecución

Requiere las dependencias del frontend (`cd frontend && npm ci`).

```bash
cd pruebas_usabilidad
npm install
npx playwright install chromium     # o, con Edge instalado: NAVEGADOR=msedge
npx playwright test
```

Levanta la build de producción del frontend en el puerto 4174. Las capturas se guardan en `docs/usabilidad/capturas/` y las medidas en `docs/usabilidad/resultados/` (cambiable con `SALIDA_USABILIDAD`).

## Lighthouse (login)

Lighthouse no puede iniciar sesión, así que solo se mide la pantalla de inicio. Ver el procedimiento en [docs/usabilidad/informe-usabilidad.md](../docs/usabilidad/informe-usabilidad.md).

## Límites

Son pruebas automáticas. No sustituyen la prueba con usuarios: ver [guion-usuarios.md](../docs/usabilidad/guion-usuarios.md).
