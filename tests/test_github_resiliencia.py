"""Cobertura parcial de CP-02: HTTP controlado y conservación de evidencia."""
import json
import urllib.error
from unittest.mock import Mock

import pytest

from app.modulos.evidencias.adaptadores.github.cliente import GitHubClient, GitHubError, RateLimitError
import sync_github as sg


@pytest.mark.parametrize("codigo", [403, 429])
def test_limite_http_se_convierte_en_error_controlado(monkeypatch, codigo):
    error = urllib.error.HTTPError(
        "https://api.github.com/rate_limit", codigo, "limite",
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "2000000000"}, None,
    )
    monkeypatch.setattr("urllib.request.urlopen", Mock(side_effect=error))
    with pytest.raises(RateLimitError) as capturado:
        GitHubClient().rate_limit()
    assert capturado.value.reset_epoch == 2000000000


@pytest.mark.parametrize("error", [
    urllib.error.HTTPError("https://api.github.com", 404, "no existe", {}, None),
    urllib.error.URLError("sin conexion"),
])
def test_fallo_api_se_convierte_en_error_controlado(monkeypatch, error):
    monkeypatch.setattr("urllib.request.urlopen", Mock(side_effect=error))
    with pytest.raises(GitHubError):
        GitHubClient().rate_limit()


@pytest.mark.parametrize("error,tipo", [
    (RateLimitError("limite"), "rate_limit"),
    (GitHubError("sin conexion"), "error_api"),
])
def test_fallo_conserva_datos_y_continua_con_otro_equipo(tmp_path, monkeypatch, error, tipo):
    monkeypatch.setattr(sg, "DIR_DATOS", str(tmp_path))
    anterior = {
        "commits": [{"autor": "ana", "fecha": "2026-09-28T10:00:00Z"}],
        "pull_requests": [{"numero": 1}], "issues": [{"numero": 2}],
        "ramas": ["main"], "consultado": "2026-09-28T12:00:00Z",
        "metricas": {"commits_total": 1}, "estado_fuente": "ok",
    }
    archivo = tmp_path / "github_equipo_a.json"
    archivo.write_text(json.dumps(anterior), encoding="utf-8")
    cliente = Mock()
    cliente.actividad_repo.side_effect = [error, {
        "commits": [], "pull_requests": [], "issues": [], "ramas": [],
    }]
    resumen = sg.sincronizar(cliente, [
        {"nombre": "Equipo A", "repositorio": "demo/a"},
        {"nombre": "Equipo B", "repositorio": "demo/b"},
    ])
    assert sg.leer_json(str(archivo)) == {**anterior, "estado_fuente": "degradada"}
    assert [e["estado_fuente"] for e in resumen["equipos"]] == ["degradada", "ok"]
    assert resumen["incidencias"][0]["tipo"] == tipo
    if tipo == "rate_limit":
        assert resumen["incidencias"][0]["reintento_en_segundos"] == 60
    assert sg.leer_json(str(tmp_path / "resumen_github.json")) == resumen
