-- Las 10 evidencias del proyecto demo (5 commits + 5 tareas)
SELECT f.tipo AS fuente, e.id_externo, e.autor, e.fecha, e.descripcion
FROM evidencia e
JOIN fuente f ON f.id = e.fuente_id
WHERE e.proyecto_id = (SELECT id FROM proyecto WHERE nombre = 'Proyecto demo TA-010')
ORDER BY f.tipo, e.fecha;

-- Comprobación de "sin campos vacíos": vacios debe ser 0
SELECT count(*) AS total,
       count(*) FILTER (WHERE autor IS NULL OR btrim(autor) = ''
                          OR btrim(id_externo) = '' OR btrim(descripcion) = '') AS vacios
FROM evidencia
WHERE proyecto_id = (SELECT id FROM proyecto WHERE nombre = 'Proyecto demo TA-010');