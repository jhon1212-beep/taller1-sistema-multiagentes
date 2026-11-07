import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PAYLOADS_SQL = ["' OR '1'='1", "1; DROP TABLE docente;--", "' UNION SELECT NULL--", "admin'--"]

@pytest.mark.parametrize("payload", PAYLOADS_SQL)
def test_payload_sql_no_causa_error_500(payload):
    # Cambia la ruta por tus endpoints reales con parámetros (ej. /proyectos/{id}, /login)
    for ruta in ["/health", f"/health?q={payload}"]:
        r = client.get(ruta)
        assert r.status_code < 500

def test_docs_no_filtra_stacktrace():
    r = client.get("/ruta-que-no-existe")
    assert r.status_code == 404
    assert "Traceback" not in r.text

def test_cabeceras_basicas():
    r = client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"  # fallará hasta agregar middleware