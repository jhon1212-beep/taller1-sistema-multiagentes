# Métricas de viabilidad · semana 10 · 2026-11-04T04:38:33+00:00

## A. Exactitud del motor (dataset TA-017)

| Proyecto | Alertas esperadas | Obtenidas | Precisión | Exhaustividad | Indicadores iguales al JSON |
|---|---|---|---|---|---|
| proyecto_1 | 6 | 6 | 100.0 % | 100.0 % | 3/4 |
| proyecto_2 | 7 | 7 | 100.0 % | 100.0 % | 3/4 |

## B. Tiempo del grafo

- Grafo completo sin latencia: media 32.8 ms, p95 44.3 ms (n=5).
- Con 300 ms por fuente: paralelo 349.5 ms frente a secuencial 907.6 ms (x2.6).

## C. Resiliencia

Cortes completados con una fuente caída: 3/3.

## D. Privacidad

0 nombres reales en 13 prompts.

## E. API (local (TestClient + PostgreSQL 16), 10 peticiones por ruta)

| Ruta | Media (ms) | p50 | p95 | Máx. | Errores | < 2 s |
|---|---|---|---|---|---|---|
| POST /consolidacion | 1368.4 | 1277.5 | 1945.8 | 1945.8 | 0 | Sí |
| GET /indicadores | 1084.7 | 716.4 | 4181.8 | 4181.8 | 0 | No |
| GET /alertas | 784.4 | 778.9 | 816.9 | 816.9 | 0 | Sí |
| GET /historial | 1156.9 | 1153.5 | 1184.0 | 1184.0 | 0 | Sí |

## F. Costo

S/ 0 · llamadas a Gemini por corte: {1: 6, 2: 7} (límite gratuito 20/día).
