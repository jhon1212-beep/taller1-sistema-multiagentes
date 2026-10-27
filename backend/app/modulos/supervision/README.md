# Supervision module

## TA-015 and TA-023
`START -> supervisor -> [github_agent | notion_agent | drive_agent] -> consolidate -> evaluate -> explain -> END`.

- `supervisor`: valida las referencias de las fuentes y la fecha de corte.
- `github_agent`, `notion_agent`, `drive_agent`: obtienen evidencias y registran fallos independientes.
- `consolidate`: une evidencias y elimina duplicados por fuente e identificador.
- `evaluate`: ejecuta `motor_indicadores.evaluar` sin LLM para I1–I4 y R1–R4.
- `explain`: construye contexto seudonimizado y usa el contrato `GeneradorExplicacion`.

## Modules
- `motor_indicadores.py`: motor determinista elegido para TA-023; `motor.py` se conserva sin cambiar hasta la decisión del equipo.
- `pseudonymizer.py`: sustituye autores por `Member N` y limpia nombres conocidos en las descripciones.
- `adaptadores/gemini.py`: prompt y llamada a Gemini; `max_retries=0`.
- `adaptadores/resilient.py`: respaldo con plantilla ante 429 u otro error.
- `adaptadores/plantilla.py`: explicación sin LLM, compatible con `contexto` opcional.

## Run
```powershell
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer template
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer gemini
python backend/scripts/run_supervisor.py --source dataset --project 2 --explainer gemini-429
```

## Test
```powershell
python -m pytest -q
python -m pytest tests/unit/test_pseudonymizer.py tests/unit/test_explanation_generators.py tests/integration/test_explainable_alerts.py -v
```

## Safety
No se imprimen claves API. El prompt incluye únicamente campos seleccionados y nombres conocidos sustituidos. La protección es específica de los nombres de los autores detectados; para información real adicional se requiere un control de privacidad más amplio.
