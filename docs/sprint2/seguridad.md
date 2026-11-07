# Pruebas de Seguridad - Sprint 2

| ID Prueba | Qué se prueba | Herramienta | Resultado | Hallazgo y corrección | Evidencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SEG-01 | Dependencias | pip-audit / npm audit |Fallido (17 vulnerabilidades encontradas) |Hallazgo: pyjwt 2.13.0 en backend y vite/source-map-js en frontend tienen vulnerabilidades altas. Corrección: Se actualizó pyjwt a 2.15.0 y se ejecutó npm audit fix. | SEG_audit.txt |
| SEG-02 | Inyección SQL | pytest + sqlmap | | | SEG_sqlmap.txt |
| SEG-03 | Escaneo general | OWASP ZAP | | | SEG_zap.html |
| SEG-04 | Rate limiting LLM | pytest | | | captura |
| SEG-05 | Prompt injection | commit malicioso | | | traza LangSmith |