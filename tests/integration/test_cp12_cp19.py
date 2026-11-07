"""TA-049 · Automatización de CP-12 a CP-19 (pruebas de integración del Sprint 2).

Un caso por cada CP, con el identificador en el nombre de la prueba, para que el
reporte de pytest en el CI (tests/resumen_cp.py) muestre cada caso en su fila.
Usan los componentes reales (Supervisor, motor, explicadores y Agente de Validación)
con el dataset controlado de TA-017: sin red, sin claves y sin base de datos.

    CP-12  R1  tarea vencida                        proyecto 2, con las evidencias
    CP-13  R2  tarea en curso sin ediciones         que la originan
    CP-14  R3  repositorio sin commits
    CP-15  R4  carpeta de Drive sin cambios
    CP-16  el prompt de Gemini no lleva nombres reales   (*)
    CP-17  validación funcional PASS/FAIL registrada y consultable
    CP-18  una fuente caída no dispara alertas de inactividad   (*)
    CP-19  error 429 de Gemini: respaldo con la plantilla

(*) La definición de CP-16 y CP-18 no está en el repositorio. Se asignó por los
criterios de aceptación de docs/specs/TA-023.md y las reglas de comportamiento de
ese documento; confirmar con el plan de pruebas del equipo.
"""
import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langsmith")

from langsmith import tracing_context

from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.supervision.adaptadores.gemini import GeminiExplanationGenerator
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.adaptadores.resilient import RATE_LIMIT, ResilientExplanationGenerator
from app.modulos.supervision.grafo.supervisor import (
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.validacion.adaptadores.falso import EjecutorE2EFalso
from app.modulos.validacion.adaptadores.memoria import RepositorioValidacionesMemoria
from app.modulos.validacion.dominio import SolicitudValidacion
from app.modulos.validacion.servicio import AgenteValidacion

CORTE = "2026-10-12T23:59:59-05:00"
REFERENCIAS = {"github": "repo-demo", "notion": "base-demo", "drive": "folder-demo"}
NOMBRES_REALES = ["Elena", "Ríos", "Carlos", "León"]  # integrantes del proyecto 2


class LLMFalso:
    """Sustituye a Gemini: guarda los prompts y, si se indica, falla."""

    def __init__(self, error=None):
        self.error, self.prompts = error, []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return type("Respuesta", (), {"text": "Explicación redactada por el modelo."})()


class ErrorLimite(Exception):
    status_code = 429


@pytest.fixture(autouse=True)
def sin_trazas():
    with tracing_context(enabled=False):
        yield


def consolidar(explicador=None, adaptadores=None):
    """Ejecuta el Supervisor sobre el proyecto 2, que dispara R1, R2, R3 y R4."""
    if adaptadores is None:
        adaptadores = {n: FuenteEvidenciaDataset(fuente=n) for n in REFERENCIAS}
    grafo = build_supervisor_graph(adaptadores, explainer=explicador)
    return to_consolidated_report(grafo.invoke(build_supervisor_input(2, CORTE, REFERENCIAS)))


def alertas_de(informe, regla):
    return [a for a in informe["alertas"] if a["regla"] == regla]


def comprobar_regla(regla, fuente, ids_esperados):
    alertas = alertas_de(consolidar(), regla)
    assert {a["fuente"] for a in alertas} == {fuente}
    assert {i for a in alertas for i in a["evidencia_ids"]} == ids_esperados
    assert len(alertas) == len(ids_esperados), "una alerta por evidencia"
    assert all(a["explicacion"] and a["origen_explicacion"] == "plantilla" for a in alertas)


def test_cp12_r1_tarea_vencida_con_su_evidencia():
    comprobar_regla("R1", "notion", {"tarea-p2-04", "tarea-p2-07"})


def test_cp13_r2_tarea_en_curso_sin_ediciones_con_su_evidencia():
    comprobar_regla("R2", "notion", {"tarea-p2-04", "tarea-p2-05", "tarea-p2-06"})


def test_cp14_r3_repositorio_sin_commits_con_su_evidencia():
    comprobar_regla("R3", "github", {"31f68efa64c129a123afda04f2f1c97aa737cc46"})


def test_cp15_r4_carpeta_de_drive_sin_cambios_con_su_evidencia():
    comprobar_regla("R4", "drive", {"archivo-p2-06"})


def test_cp16_el_prompt_de_gemini_no_lleva_nombres_reales():
    llm = LLMFalso()
    informe = consolidar(GeminiExplanationGenerator(llm, min_interval_seconds=0))
    enviado = "\n".join(llm.prompts)
    assert len(llm.prompts) == len(informe["alertas"]) == 7
    assert not [n for n in NOMBRES_REALES if n in enviado]
    assert "Member 1" in enviado
    assert {a["origen_explicacion"] for a in informe["alertas"]} == {"gemini"}


def test_cp17_validacion_funcional_pass_y_fail_registradas_y_consultables():
    repositorio = RepositorioValidacionesMemoria()
    agente = AgenteValidacion(EjecutorE2EFalso(), repositorio)
    agente.validar(SolicitudValidacion(2, "https://demo.test", "h1"))
    agente.validar(SolicitudValidacion(2, "https://falla.test", "h1"))

    assert repositorio.contar(2) == {"PASS": 1, "FAIL": 1}
    historial = repositorio.listar(2)
    assert {g.resultado.resultado for g in historial} == {"PASS", "FAIL"}
    assert all(g.resultado.run_id_actions is not None for g in historial), "RN-003: lleva su ejecución"
    fail = next(g for g in historial if g.resultado.resultado == "FAIL")
    pass_ = next(g for g in historial if g.resultado.resultado == "PASS")
    assert fail.resultado.captura_url and pass_.resultado.captura_url is None
    assert repositorio.ultima(2).id == max(g.id for g in historial)


def test_cp18_una_fuente_caida_no_dispara_alertas_de_inactividad():
    class Caida:
        def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
            raise ConnectionError("GitHub no responde")

    adaptadores = {n: FuenteEvidenciaDataset(fuente=n) for n in REFERENCIAS}
    adaptadores["github"] = Caida()
    informe = consolidar(adaptadores=adaptadores)
    assert informe["fuentes"]["github"]["estado"] == "fallo"
    assert alertas_de(informe, "R3") == []
    # el resto de fuentes sigue funcionando
    assert alertas_de(informe, "R1") and alertas_de(informe, "R4")


def test_cp19_error_429_de_gemini_usa_la_plantilla_y_lo_marca_en_cada_alerta():
    resiliente = ResilientExplanationGenerator(
        GeminiExplanationGenerator(LLMFalso(error=ErrorLimite("429")), min_interval_seconds=0),
        GeneradorExplicacionPlantilla(),
    )
    informe = consolidar(resiliente)
    assert {a["origen_explicacion"] for a in informe["alertas"]} == {"plantilla"}
    assert all(a["explicacion"] for a in informe["alertas"])
    assert len(resiliente.fallbacks) == 7
    assert {f["motivo"] for f in resiliente.fallbacks} == {RATE_LIMIT}
