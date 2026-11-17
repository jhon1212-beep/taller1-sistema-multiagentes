# Módulo proyectos

Carpeta reservada para el módulo `proyectos` (Product Backlog v6.0, sección 4.5).
Su dueño publica aquí su contrato (`dominio.py`, `puertos.py` y su
adaptador falso) en la semana 6.

## Fuentes del proyecto

`FUENTES_OBLIGATORIAS = ("github", "notion")` y `FUENTES_OPCIONALES = ("drive",)` en
`dominio.py`. El servicio descarta las referencias vacías antes de validar, así que
`"drive": ""`, `"drive": null` o no enviar la clave registran el proyecto sin Drive
(no se crea fila en la tabla `fuente`). Al editar se puede agregar o quitar Drive.
