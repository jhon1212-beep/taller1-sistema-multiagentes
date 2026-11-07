-- TA-018 · Historial por fecha de corte de un proyecto.
-- Una fila por corte: I1–I4, número de alertas por regla y la última
-- validación E2E (TA-021) registrada ese mismo día (hora de Lima).
-- Uso en psql:  \set proyecto 1   y luego   \i docs/sprint2/TA-018_historial.sql
SELECT i.fecha_corte,
       i.i1_pct_completadas       AS i1,
       i.i2_pct_pendientes        AS i2,
       i.i3_tareas_vencidas       AS i3,
       i.i4_dias_sin_actividad    AS i4,
       COUNT(a.id)                                  AS alertas,
       COUNT(a.id) FILTER (WHERE a.regla = 'R1')    AS r1,
       COUNT(a.id) FILTER (WHERE a.regla = 'R2')    AS r2,
       COUNT(a.id) FILTER (WHERE a.regla = 'R3')    AS r3,
       COUNT(a.id) FILTER (WHERE a.regla = 'R4')    AS r4,
       (SELECT v.resultado
          FROM validacion v
         WHERE v.proyecto_id = i.proyecto_id
           AND (v.ejecutada_en AT TIME ZONE 'America/Lima')::date = i.fecha_corte
         ORDER BY v.ejecutada_en DESC
         LIMIT 1)                                   AS validacion_e2e
  FROM indicador i
  LEFT JOIN alerta a
         ON a.proyecto_id = i.proyecto_id AND a.fecha_corte = i.fecha_corte
 WHERE i.proyecto_id = :proyecto
 GROUP BY i.id
 ORDER BY i.fecha_corte;
