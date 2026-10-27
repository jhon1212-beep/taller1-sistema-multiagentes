"""TA-021: Agente de Validación y ejecutor de GitHub Actions (sin red)."""

import pytest

from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso
from app.modulos.validacion.adaptadores.github_actions import EjecutorE2EGitHubActions
from app.modulos.validacion.dominio import (
    ErrorInfraestructuraValidacion,
    ResultadoValidacion,
    SolicitudValidacion,
)
from app.modulos.validacion.servicio import AgenteValidacion

SOLICITUD = SolicitudValidacion(proyecto_id=7, url_publica="https://demo.test", elemento_verificar="h1")


class GitHubFalso:
    """Simula la API de GitHub: guarda lo que recibe y responde en orden."""

    def __init__(self, *, dispatch=204, conclusion="success", estados=("in_progress", "completed"), aparece=True):
        self.llamadas: list[tuple[str, str, dict | None]] = []
        self.dispatch, self.conclusion, self.estados, self.aparece = dispatch, conclusion, list(estados), aparece
        self.correlacion = None

    def __call__(self, metodo, url, cuerpo):
        self.llamadas.append((metodo, url, cuerpo))
        if metodo == "POST":
            if cuerpo:
                self.correlacion = cuerpo["inputs"]["correlacion"]
            return self.dispatch, None
        if "/runs?" in url:
            nombre = f"E2E {self.correlacion} - proyecto 7" if self.aparece else "E2E otro - proyecto 1"
            return 200, {"workflow_runs": [{"id": 555, "name": nombre}]}
        estado = self.estados.pop(0) if len(self.estados) > 1 else self.estados[0]
        return 200, {
            "id": 555, "status": estado, "conclusion": self.conclusion if estado == "completed" else None,
            "html_url": "https://github.com/o/r/actions/runs/555",
            "run_started_at": "2026-10-27T10:00:00Z", "created_at": "2026-10-27T10:00:00Z",
            "updated_at": "2026-10-27T10:00:42Z",
        }


def ejecutor(gh, **kw):
    return EjecutorE2EGitHubActions(
        repositorio="o/r", token="t", transporte=gh, espera=lambda s: None,
        tiempo_max_s=20, intervalo_s=5, intentos_localizar=3, **kw,
    )


def test_pass_cuando_el_run_termina_en_success():
    gh = GitHubFalso(conclusion="success")
    r = ejecutor(gh).ejecutar(SOLICITUD)
    assert (r.resultado, r.run_id_actions, r.duracion_ms, r.captura_url) == ("PASS", 555, 42_000, None)


def test_fail_es_resultado_no_excepcion_y_lleva_enlace_a_artefactos():
    r = ejecutor(GitHubFalso(conclusion="failure")).ejecutar(SOLICITUD)
    assert r.resultado == "FAIL"
    assert r.captura_url.endswith("/runs/555#artifacts")


def test_el_disparo_envia_los_parametros_del_workflow():
    gh = GitHubFalso()
    ejecutor(gh).ejecutar(SOLICITUD)
    metodo, url, cuerpo = gh.llamadas[0]
    assert (metodo, url.endswith("/repos/o/r/actions/workflows/e2e.yml/dispatches")) == ("POST", True)
    assert cuerpo["ref"] == "main"
    assert {k: cuerpo["inputs"][k] for k in ("url_publica", "elemento_verificar", "proyecto_id")} == {
        "url_publica": "https://demo.test", "elemento_verificar": "h1", "proyecto_id": "7",
    }
    assert len(cuerpo["inputs"]["correlacion"]) == 12


def test_espera_hasta_que_el_run_se_completa():
    gh = GitHubFalso(estados=("queued", "in_progress", "completed"))
    ejecutor(gh).ejecutar(SOLICITUD)
    consultas_run = [u for m, u, _ in gh.llamadas if u.endswith("/runs/555")]
    assert len(consultas_run) == 3


@pytest.mark.parametrize(
    "gh, mensaje",
    [
        (GitHubFalso(dispatch=404), "rechazó el disparo"),
        (GitHubFalso(aparece=False), "No apareció"),
        (GitHubFalso(conclusion="cancelled"), "sin PASS ni FAIL"),
        (GitHubFalso(estados=("in_progress",)), "no terminó"),
    ],
)
def test_fallos_de_infraestructura_lanzan_excepcion(gh, mensaje):
    with pytest.raises(ErrorInfraestructuraValidacion, match=mensaje):
        ejecutor(gh).ejecutar(SOLICITUD)


def test_sin_token_no_se_puede_crear_el_ejecutor():
    with pytest.raises(ErrorInfraestructuraValidacion):
        EjecutorE2EGitHubActions(repositorio="o/r", token="")


class RegistroEnMemoria:
    def __init__(self):
        self.filas: list[ResultadoValidacion] = []

    def registrar(self, r):
        self.filas.append(r)
        return len(self.filas)


def test_el_agente_registra_pass_y_fail():
    registro = RegistroEnMemoria()
    agente = AgenteValidacion(EjecutorE2EFalso(), registro)
    id_pass, r_pass = agente.validar(SOLICITUD)
    id_fail, r_fail = agente.validar(SolicitudValidacion(7, "https://falla.test", "h1"))
    assert (r_pass.resultado, r_fail.resultado) == ("PASS", "FAIL")
    assert [f.resultado for f in registro.filas] == ["PASS", "FAIL"] and (id_pass, id_fail) == (1, 2)


def test_un_fallo_de_infraestructura_no_se_registra():
    registro = RegistroEnMemoria()
    agente = AgenteValidacion(ejecutor(GitHubFalso(dispatch=500)), registro)
    with pytest.raises(ErrorInfraestructuraValidacion):
        agente.validar(SOLICITUD)
    assert registro.filas == []
