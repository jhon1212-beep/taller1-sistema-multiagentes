-- RN-003 · Trazabilidad de resultados. Cada consulta debe devolver 0 en la columna "sin_traza".
-- Uso: SQL Editor de Neon o psql sobre la base que se quiere auditar.

-- 1) Alertas sin evidencia de origen (o con una evidencia que ya no existe)
SELECT COUNT(*) AS total_alertas,
       COUNT(*) FILTER (WHERE e.id IS NULL) AS sin_traza
FROM alerta a LEFT JOIN evidencia e ON e.id = a.evidencia_id;

-- 2) Alertas cuya evidencia es de otro proyecto
SELECT COUNT(*) AS sin_traza
FROM alerta a JOIN evidencia e ON e.id = a.evidencia_id
WHERE e.proyecto_id <> a.proyecto_id;

-- 3) Alertas cuya evidencia no es de la fuente que exige su regla (R1/R2 Notion, R3 GitHub, R4 Drive)
SELECT COUNT(*) AS sin_traza
FROM alerta a
JOIN evidencia e ON e.id = a.evidencia_id
JOIN fuente f ON f.id = e.fuente_id
WHERE (a.regla IN ('R1', 'R2') AND f.tipo <> 'notion')
   OR (a.regla = 'R3' AND f.tipo <> 'github')
   OR (a.regla = 'R4' AND f.tipo <> 'drive');

-- 4) Validaciones sin el id de su ejecución en GitHub Actions
SELECT COUNT(*) AS total_validaciones,
       COUNT(*) FILTER (WHERE run_id_actions IS NULL OR run_id_actions <= 0) AS sin_traza
FROM validacion;

-- 5) Validaciones FAIL sin captura (informativo: la captura depende del artefacto de Actions)
SELECT COUNT(*) FILTER (WHERE resultado = 'FAIL') AS total_fail,
       COUNT(*) FILTER (WHERE resultado = 'FAIL' AND captura_url IS NULL) AS fail_sin_captura
FROM validacion;
