# -*- coding: utf-8 -*-
"""TA-013 · Pruebas de integración CP-01 a CP-08 (plan de pruebas TA-003).

Se ejecutan sin red ni base de datos, sobre el dataset controlado de TA-017
(proyecto 1 "activo", proyecto 2 "estancado"; fecha de corte
2026-10-13T04:59:59Z) y los componentes reales ya construidos: grafo
supervisor (TA-015), motor de indicadores y reglas (TA-019), API de
proyectos y tareas (HU-002 / HU-004) y contrato de autenticación (AR-04).

Convenciones del informe (pytest -rs):
  * PASSED  = lo verificable hoy cumple el resultado esperado del caso.
  * SKIPPED = "BLOQUEADO": la parte del caso que depende de algo no
              implementado todavía. Cada skip dice qué falta.

Un CI verde NO equivale a la aceptación completa de CP-01..CP-08 (ver
docs/sprint1/TA-003.md): los SKIPPED son los pendientes reales.
"""
from datetime import datetime, timezone

import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langsmith")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient
from langsmith import tracing_context

from app.main import app
from app.modulos.autenticacion.adaptadores.falso import CLAVE_DEMO, ServicioAutenticacionFalso
from app.modulos.autenticacion.dominio import SesionInvalida
from app.modulos.evidencias.adaptadores.dataset import FuenteEvidenciaDataset
from app.modulos.evidencias.adaptadores.github.cliente import RateLimitError
from app.modulos.evidencias.dataset import cargar_dataset, fecha_corte_demo
from app.modulos.evidencias.dominio import EvidenciaNotion
from app.modulos.evidencias.rutas_tareas import obtener_fuente_tareas
from app.modulos.proyectos.adaptadores.memoria import RepositorioProyectosMemoria
from app.modulos.proyectos.dominio import Integrante, Proyecto, ProyectoNoEncontrado
from app.modulos.proyectos.rutas import docente_actual, obtener_servicio
from app.modulos.proyectos.servicio import ServicioProyectos
from app.modulos.supervision.grafo.supervisor import (
    build_supervisor_graph,
    build_supervisor_input,
    to_consolidated_report,
)
from app.modulos.supervision.motor import evaluar

CORTE = fecha_corte_demo()
REFERENCIAS = {"github": "demo/repo", "notion": "base-demo", "drive": "carpeta-demo"}


@pytest.fixture(autouse=True)
def sin_trazas():
    with tracing_context(enabled=False):
        yield


def _adaptadores(**sobre):
    base = {f: FuenteEvidenciaDataset(f) for f in ("github", "notion", "drive")}
    base.update(sobre)
    return base


def _supervisar(proyecto_id, corte=CORTE, adaptadores=None):
    grafo = build_supervisor_graph(adaptadores or _adaptadores())
    entrada = build_supervisor_input(proyecto_id, corte, REFERENCIAS)
    return to_consolidated_report(grafo.invoke(entrada))


def _de(reporte, fuente):
    return [e for e in reporte["evidencias"] if e["fuente"] == fuente]


# =========================================================================
# CP-01 · Conexión con GitHub y lectura de actividad (HU-001)
# =========================================================================
def test_cp01_commits_con_autor_y_fecha_por_proyecto():
    r = _supervisar(1)
    commits = _de(r, "github")

    assert r["fuentes"]["github"]["estado"] == "ok"
    assert len(commits) == 20
    assert all(c["autor"] and c["fecha"] and len(c["id_externo"]) == 40 for c in commits)
    assert all(c["proyecto_id"] == 1 for c in commits)  # asociados al equipo correcto
    assert len({c["id_externo"] for c in commits}) == 20


def test_cp01_los_dos_equipos_no_se_mezclan():
    ids_1 = {c["id_externo"] for c in _de(_supervisar(1), "github")}
    ids_2 = {c["id_externo"] for c in _de(_supervisar(2), "github")}
    assert len(ids_1) == 20 and len(ids_2) == 12 and not ids_1 & ids_2


@pytest.mark.skip(reason="BLOQUEADO (parcial): el dataset solo contiene commits; PR e issues "
                         "se verifican contra la API real (docs/sprint1/pruebas-github-por-caso).")
def test_cp01_prs_e_issues_en_el_dataset():
    ...


# =========================================================================
# CP-02 · Límite de API de GitHub (HU-001)
# =========================================================================
class GitHubLimitado:
    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        raise RateLimitError("API rate limit exceeded", reset_epoch=1_760_000_000)


def test_cp02_limite_de_github_degrada_solo_esa_fuente():
    r = _supervisar(1, adaptadores=_adaptadores(github=GitHubLimitado()))

    assert r["fuentes"]["github"]["estado"] == "fallo"
    assert "RateLimitError" in r["fuentes"]["github"]["error"]
    assert r["fuentes"]["notion"]["estado"] == "ok"
    assert r["fuentes"]["drive"]["estado"] == "ok"
    assert len(_de(r, "notion")) == 20 and len(_de(r, "drive")) == 10
    assert _de(r, "github") == []  # no se inventan commits


def test_cp02_otro_equipo_sigue_procesandose_tras_el_limite():
    adaptadores = _adaptadores(github=GitHubLimitado())
    _supervisar(1, adaptadores=adaptadores)
    r2 = _supervisar(2, adaptadores=_adaptadores())
    assert r2["fuentes"]["github"]["estado"] == "ok" and len(_de(r2, "github")) == 12


@pytest.mark.skip(reason="BLOQUEADO (parcial): el código registra reintento_en_segundos pero no "
                         "programa la ejecución futura (ver TA-003, CP-02).")
def test_cp02_reintento_programado():
    ...


# =========================================================================
# CP-03 · Gestor de tareas Notion (HU-002 / HU-004)
# =========================================================================
class NotionConCasosLimite:
    """Base con la tarea completa, sin responsable, sin fecha y sin ambos."""

    def obtener_evidencias(self, referencia, proyecto_id, *, limite=None, desde=None):
        return [
            EvidenciaNotion("notion", "t-completa", "Ana Torres", "2026-10-08T10:00:00Z",
                            "Tarea completa", proyecto_id, estado="En curso", fecha_limite="2026-10-20"),
            EvidenciaNotion("notion", "t-sin-resp", None, "2026-10-08T10:00:00Z",
                            "Sin responsable", proyecto_id, estado="Sin empezar", fecha_limite="2026-10-21"),
            EvidenciaNotion("notion", "t-sin-fecha", "Luis Vega", "2026-10-08T10:00:00Z",
                            "Sin fecha límite", proyecto_id, estado="Sin empezar", fecha_limite=None),
            EvidenciaNotion("notion", "t-sin-ambos", None, "2026-10-08T10:00:00Z",
                            "Sin responsable ni fecha", proyecto_id, estado="Sin empezar", fecha_limite=None),
        ]


@pytest.fixture
def api():
    servicio = ServicioProyectos(RepositorioProyectosMemoria())
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    app.dependency_overrides[obtener_fuente_tareas] = lambda: NotionConCasosLimite()
    cliente = TestClient(app)
    cliente.post("/proyectos", json={
        "nombre": "Proyecto CP-03", "curso": "Taller", "fecha_inicio": "2026-09-21",
        "fecha_fin": "2026-11-30", "url_publica": "https://example.org",
        "elemento_verificar": "h1", "integrantes": [{"nombre": "Ana Torres"}],
        "fuentes": {"github": "g", "notion": "base-notion", "drive": "d"},
    })
    yield cliente
    app.dependency_overrides.clear()


def test_cp03_campos_faltantes_se_identifican_sin_omitir_la_tarea(api):
    cuerpo = api.get("/proyectos/1/tareas").json()
    por_id = {t["id"]: t for t in cuerpo["tareas"]}

    assert cuerpo["estado"] == "ok" and cuerpo["total"] == 4  # ninguna se omite
    assert por_id["t-completa"]["responsable"] == "Ana Torres"
    assert por_id["t-completa"]["fecha_limite"] == "2026-10-20"
    assert por_id["t-sin-resp"]["responsable"] is None and por_id["t-sin-resp"]["fecha_limite"]
    assert por_id["t-sin-fecha"]["fecha_limite"] is None and por_id["t-sin-fecha"]["responsable"]
    assert por_id["t-sin-ambos"]["responsable"] is None and por_id["t-sin-ambos"]["fecha_limite"] is None
    assert cuerpo["resumen"]["sin_responsable"] == 2


def test_cp03_dataset_demo_conserva_responsable_estado_y_fecha():
    tareas = _de(_supervisar(1), "notion")
    assert len(tareas) == 20
    assert all(t["estado"] in ("Sin empezar", "En curso", "Listo") for t in tareas)
    assert all(t["fecha_limite"] for t in tareas)
    assert [t["autor"] for t in tareas].count(None) == 1


# =========================================================================
# CP-04 · Documentación Google Drive (HU-003)
# =========================================================================
def test_cp04_drive_entrega_documentos_con_fecha_y_tipo():
    r = _supervisar(1)
    docs = _de(r, "drive")

    assert r["fuentes"]["drive"]["estado"] == "ok" and len(docs) == 10
    assert all(d["fecha"] and d["descripcion"] for d in docs)
    assert len({d["id_externo"] for d in docs}) == 10


@pytest.mark.skip(reason="BLOQUEADO: falta el conector real de Drive y la clasificación "
                         "existente / faltante / desactualizado con lista de entregables y umbral.")
def test_cp04_entregables_existentes_faltantes_y_desactualizados():
    ...


# =========================================================================
# CP-05 · Consolidación por equipo y semana (HU-004)
# =========================================================================
SEMANAS = ["2026-09-29T00:00:00Z", "2026-10-06T00:00:00Z", CORTE]


def test_cp05_consolidado_por_equipo_y_semana_sin_mezclar():
    previos = 0
    for corte in SEMANAS:
        r1 = _supervisar(1, corte)
        assert r1["proyecto_id"] == 1 and r1["fecha_corte"] == corte
        assert all(e["proyecto_id"] == 1 for e in r1["evidencias"])
        assert all(e["fecha"] <= corte for e in r1["evidencias"])  # nada posterior al corte
        assert r1["total_evidencias"] >= previos  # la actividad acumulada no decrece
        assert all(f["estado"] == "ok" for f in r1["fuentes"].values())
        previos = r1["total_evidencias"]
    assert previos == 50  # al corte demo está toda la evidencia del proyecto 1


def test_cp05_primera_semana_contiene_las_tres_fuentes():
    r = _supervisar(1, SEMANAS[0])
    assert {e["fuente"] for e in r["evidencias"]} == {"github", "notion", "drive"}
    assert r["fuentes"]["github"]["evidencias"] == 7
    assert r["fuentes"]["github"]["fuera_de_corte"] == 13  # los commits de semanas siguientes


def test_cp05_repetir_la_sincronizacion_no_duplica():
    a = _supervisar(1, SEMANAS[1])
    b = _supervisar(1, SEMANAS[1])
    claves_a = sorted((e["fuente"], e["id_externo"]) for e in a["evidencias"])
    claves_b = sorted((e["fuente"], e["id_externo"]) for e in b["evidencias"])
    assert claves_a == claves_b and len(claves_a) == len(set(claves_a))


@pytest.mark.skip(reason="BLOQUEADO (parcial): no existe aún la API consolidada por equipo y "
                         "semana; se verifica el consolidado del grafo de TA-015.")
def test_cp05_api_consolidada_por_equipo_y_semana():
    ...


# =========================================================================
# CP-06 · Cálculo de avance y pendientes (HU-005)
# =========================================================================
def _tareas_cp06(estados):
    return [
        EvidenciaNotion("notion", f"t{i}", "Ana", "2026-10-10T10:00:00Z", f"Tarea {i}", 1,
                        estado=e, fecha_limite="2026-10-30")
        for i, e in enumerate(estados, 1)
    ]


def test_cp06_avance_pasa_de_25_a_50_por_ciento():
    antes, _ = evaluar(_tareas_cp06(["Listo", "Sin empezar", "Sin empezar", "Sin empezar"]), CORTE)
    despues, _ = evaluar(_tareas_cp06(["Listo", "Listo", "Sin empezar", "Sin empezar"]), CORTE)

    assert antes["I1"] == 25.0 and antes["I2"] == 75.0  # una terminada, tres pendientes
    assert despues["I1"] == 50.0 and despues["I2"] == 50.0  # dos terminadas, dos pendientes


def test_cp06_dataset_demo_coincide_con_los_valores_esperados():
    esperado = cargar_dataset()["indicadores_esperados"]
    for pid in (1, 2):
        ind, _ = evaluar(FuenteEvidenciaDataset().obtener_evidencias("x", pid), CORTE)
        assert ind == esperado[str(pid)]


# =========================================================================
# CP-07 · Retrasos y semáforo de riesgo (HU-006)
# =========================================================================
def test_cp07_reglas_con_evidencia_de_origen_en_los_dos_escenarios():
    por_regla = {}
    for pid in (1, 2):
        _, alertas = evaluar(FuenteEvidenciaDataset().obtener_evidencias("x", pid), CORTE)
        por_regla[pid] = {a["regla"] for a in alertas}
        ids = {e.id_externo for e in FuenteEvidenciaDataset().obtener_evidencias("x", pid)}
        assert all(a["evidencia_ids"] and set(a["evidencia_ids"]) <= ids for a in alertas)

    assert por_regla[1] == {"R1", "R2"}  # equipo activo: sin R3 ni R4
    assert por_regla[2] == {"R1", "R2", "R3", "R4"}  # equipo estancado


def test_cp07_umbrales_en_el_limite_son_exclusivos():
    corte = "2026-10-13T04:59:59Z"
    def alerta_r2(editada):
        t = EvidenciaNotion("notion", "t", "Ana", editada, "x", 1, estado="En curso",
                            fecha_limite="2026-11-01")
        return any(a["regla"] == "R2" for a in evaluar([t], corte)[1])

    assert alerta_r2("2026-10-06T04:59:59Z") is False  # exactamente 7 días: aún no
    assert alerta_r2("2026-10-06T04:59:58Z") is True   # un segundo más


@pytest.mark.skip(reason="BLOQUEADO: la clasificación verde/amarillo/rojo y sus umbrales aprobados "
                         "no están implementados; hoy solo existen las alertas R1-R4.")
def test_cp07_semaforo_de_riesgo():
    ...


# =========================================================================
# CP-08 · Roles y aislamiento
# =========================================================================
def _proyecto(docente_id, nombre):
    from datetime import date
    return Proyecto(
        docente_id=docente_id, nombre=nombre, curso="Taller",
        fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
        url_publica="https://example.org", elemento_verificar="h1",
        integrantes=[Integrante("Ana")], fuentes={"github": "g", "notion": "n", "drive": "d"},
    )


def test_cp08_un_docente_no_accede_a_proyectos_de_otro():
    servicio = ServicioProyectos(RepositorioProyectosMemoria())
    propio = servicio.registrar(_proyecto(1, "Del docente 1"))

    assert servicio.obtener(1, propio.id).nombre == "Del docente 1"
    with pytest.raises(ProyectoNoEncontrado):
        servicio.obtener(2, propio.id)  # cambiar el identificador no revela datos ajenos
    assert servicio.listar(2) == []


def test_cp08_api_rechaza_el_acceso_cruzado_con_404(api):
    app.dependency_overrides[docente_actual] = lambda: 2
    assert api.get("/proyectos/1/tareas").status_code == 404
    assert api.get("/proyectos/1").status_code == 404


def test_cp08_sin_sesion_valida_no_hay_docente():
    auth = ServicioAutenticacionFalso()
    sesion = auth.iniciar_sesion("docente1@demo.test", CLAVE_DEMO)
    assert auth.obtener_docente(sesion.token).id == 1
    with pytest.raises(SesionInvalida):
        auth.obtener_docente("token-inventado")  # anónimo / token falso
    auth.cerrar_sesion(sesion.token)
    with pytest.raises(SesionInvalida):
        auth.obtener_docente(sesion.token)


@pytest.mark.skip(reason="BLOQUEADO: el servidor aún usa docente_actual() = 1 (temporal) y no "
                         "hay rol estudiante; falta enlazar AR-04 a las rutas y el control por rol.")
def test_cp08_estudiante_solo_consulta_su_equipo_y_anonimo_es_rechazado():
    ...
