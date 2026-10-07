# TA-011 · Revisión de consistencia de la interfaz

**Estimación:** 0,5 SP · 2 h · **Equipo:** MONDRAGÓN · **Fecha:** 06/10/2026
**Alcance:** `frontend/src/**` y `docs/Prototipo_Agentes_Seguimiento.html`, contra el
sistema visual `frontend/src/estilos/tokens.css` (EN-UI-001).

La revisión no es una opinión: se apoya en una comprobación automática,
`scripts/auditar_ui.py`, que se puede volver a ejecutar en cualquier momento.

```bash
python scripts/auditar_ui.py
```

## 1. Resultado de la comprobación automática

| Métrica | Valor |
|---|---|
| Archivos de interfaz revisados | 15 |
| Tokens declarados en `tokens.css` | 39 |
| Tokens efectivamente usados | 39 |
| Tokens declarados pero sin usar | **0** |
| Tokens usados pero no declarados | **0** |
| Colores escritos a mano (hex) | **43** |
| `font-size` en px escritos a mano | **34** |

Detalle completo en `docs/sprint1/TA-011_auditoria.json`.

## 2. Hallazgos

### H-01 · El prototipo HTML no consume el sistema visual — *severidad alta*

`docs/Prototipo_Agentes_Seguimiento.html` enlaza `tokens.css`, pero define su
estilo con valores propios: **43 colores** y **34 tamaños de fuente** escritos
directamente en el archivo. El 100 % de los valores a mano detectados está ahí.

Esto contradice la regla declarada en el encabezado de `tokens.css`
(«no debe haber valores hardcodeados en la vista») y crea dos sistemas de
estilo en paralelo: si se cambia un color del sistema visual, el prototipo
no se entera.

| Archivo | Colores a mano | `font-size` a mano |
|---|---|---|
| `docs/Prototipo_Agentes_Seguimiento.html` | 43 | 34 |
| `frontend/src/**` (base React) | 0 | 0 |

**Corrección aplicada:** la base React (TA-005) se construyó consumiendo solo
tokens, por lo que la interfaz que se seguirá desarrollando ya nace consistente.

**Pendiente de decisión del equipo:** qué hacer con el prototipo HTML. Son dos
caminos razonables y conviene elegir uno explícitamente:

1. **Declararlo histórico.** Es la maqueta que sirvió para validar el alcance y
   ya cumplió su función. Se deja como está, con una nota al inicio que diga que
   la interfaz vigente es la de `frontend/`. Coste: 0.
2. **Refactorizarlo** para que use los tokens. Solo tiene sentido si se va a
   seguir presentando el HTML en vez del frontend React. Coste estimado: 2 h.

Recomendación: la opción 1. Mantener dos interfaces al día duplica el trabajo
sin aportar nada, ahora que la base React funciona.

### H-02 · Cobertura de tokens correcta — *sin acción*

No hay tokens muertos ni tokens usados sin declarar. Esto importa porque un
token usado sin declarar no falla de forma visible: el navegador simplemente
no aplica el estilo y el defecto pasa desapercibido. La comprobación queda
automatizada para que no se cuele en el futuro.

### H-03 · Decisiones de consistencia adoptadas en la base React — *aplicadas*

Durante TA-005 se unificaron criterios que en el prototipo estaban dispersos:

| Elemento | Antes (prototipo) | Ahora (base React) |
|---|---|---|
| Título de tarjeta | `h3` con `--fs-lg` | `h3` con `--fs-h3`, que es el token creado para eso |
| Indicador de atención | texto en `--ink` | texto en `--warn`, igual que `ok` y `bad` usan el suyo |
| Fondo de aviso | `--soft` directo | `--infobg`, que es el token semántico |
| Espaciado | píxeles sueltos | escala `--sp-1` a `--sp-6` |
| Radio de avisos | sin radio | `--r-md` |
| Foco de teclado | `outline-offset` sin contorno visible | `:focus-visible` con contorno explícito |

## 3. Observación sobre el alcance de esta revisión

La comprobación automática detecta valores escritos a mano y tokens
descuadrados. **No** sustituye una revisión visual: no juzga si un contraste es
suficiente, si la jerarquía tipográfica se entiende o si un flujo es claro.
Para eso hace falta mirar las pantallas, idealmente con alguien que no las haya
construido.

Dos puntos que quedan fuera de esta revisión y conviene atender:

- **Contraste.** No se midió el ratio de contraste contra WCAG AA. El indicador
  de atención (`--warn` `#e0a100` sobre `--warnbg` `#fff6da`) es el candidato
  más probable a quedarse corto y debería medirse.
- **Comportamiento en móvil.** Hay puntos de corte definidos en `base.css`, pero
  no se probaron en un dispositivo real.

## 4. Cómo repetir la revisión

`scripts/auditar_ui.py` devuelve código de salida 1 si encuentra un token usado
sin declarar, de modo que puede conectarse al workflow de CI (TA-035) para que
el problema se detecte en cada pull request en vez de en una revisión manual.
