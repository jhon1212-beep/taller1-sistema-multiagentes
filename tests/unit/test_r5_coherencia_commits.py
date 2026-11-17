"""R5: posible incoherencia entre el mensaje de un commit y lo que cambió.

La regla es determinista (coherencia.py) y conservadora: solo marca casos
objetivos y nunca decide con un LLM. Gemini o la plantilla solo redactan.
"""
from __future__ import annotations

import pytest

from app.modulos.evidencias.adaptadores.github import adaptador
from app.modulos.evidencias.adaptadores.github.cliente import GitHubClient, GitHubError
from app.modulos.evidencias.dominio import EvidenciaGitHub
from app.modulos.supervision.adaptadores.gemini import build_batch_prompt
from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
from app.modulos.supervision.coherencia import revisar_commit
from app.modulos.supervision.motor_indicadores import evaluar_reglas

CORTE = "2026-10-12T23:59:59-05:00"


# -- la regla -------------------------------------------------------------------

@pytest.mark.parametrize("mensaje,archivos,adds,dels,esperado", [
    ("feat: historial completo", [], 0, 0, "no cambia el contenido"),
    ("refactor: mover carpeta", ["a/x.py"], 0, 0, "no cambia el contenido"),
    ("test: pruebas del dashboard", ["frontend/src/Dashboard.jsx"], 10, 2, "dice agregar pruebas"),
    ("Agrega pruebas de login", ["README.md"], 3, 0, "dice agregar pruebas"),
    ("feat: agente Drive", ["docs/drive.md", "docs/captura.png"], 40, 0, "solo se modificó documentación"),
    ("Implementa el login", ["README.md"], 5, 1, "solo se modificó documentación"),
    ("fix: corrige Login.jsx", ["frontend/src/paginas/Proyectos.jsx"], 4, 4, "«Login.jsx»"),
])
def test_casos_incoherentes_dan_un_motivo(mensaje, archivos, adds, dels, esperado):
    motivo = revisar_commit(mensaje, archivos, adds, dels)
    assert motivo and esperado in motivo
    assert mensaje[:40] in motivo  # el docente ve qué decía el commit


@pytest.mark.parametrize("mensaje,archivos", [
    ("feat: login con JWT", ["backend/app/modulos/autenticacion/rutas.py"]),
    ("test: pruebas del login", ["tests/test_login.py"]),
    ("Agrega pruebas E2E", ["frontend/e2e/login.spec.js"]),
    ("docs: actualiza README", ["README.md"]),
    ("fix: corrige Login.jsx", ["frontend/src/paginas/Login.jsx"]),
    ("fix: corrige login.JSX y estilos", ["frontend/src/paginas/Login.jsx", "frontend/src/base.css"]),
    ("chore: limpieza", ["archivo_temporal.txt"]),
    ("Merge pull request #12", ["a.py"]),  # mensaje sin afirmaciones verificables
    ("TA-003: publicar plan de pruebas", ["docs/sprint1/TA-003.md"]),  # documenta pruebas
    ("docs: agrega pruebas de la API por caso", ["docs/pruebas-github/caso1.docx"]),
    ("Pruebas de carga con Locust", ["pruebas_carga/locustfile.py"]),
    ("Create test", ["config/test"]),
])
def test_casos_coherentes_no_dan_motivo(mensaje, archivos):
    assert revisar_commit(mensaje, archivos, 5, 1) is None


def test_merges_y_commits_sin_detalle_no_se_evaluan():
    assert revisar_commit("feat: todo", [], 0, 0, es_merge=True) is None
    assert revisar_commit("feat: todo", None) is None


def test_el_motivo_resume_listas_largas_de_archivos():
    archivos = [f"docs/f{i}.md" for i in range(9)]
    motivo = revisar_commit("feat: modulo nuevo", archivos, 9, 0)
    assert "y 5 más" in motivo


# -- en el motor ---------------------------------------------------------------

def _commit(sha, mensaje, archivos, fecha="2026-10-12T10:00:00Z", **kw):
    return EvidenciaGitHub(fuente="github", id_externo=sha, autor="Ana Torres", fecha=fecha,
                           descripcion=mensaje, proyecto_id=1, archivos=archivos,
                           adiciones=kw.get("adiciones", 5), eliminaciones=kw.get("eliminaciones", 1))


def test_motor_emite_r5_solo_para_commits_incoherentes_de_la_ultima_semana():
    commits = [
        _commit("a" * 40, "test: pruebas del login", ["README.md"]),                 # R5
        _commit("b" * 40, "feat: login", ["backend/app/login.py"]),                 # coherente
        _commit("c" * 40, "test: pruebas viejas", ["README.md"], fecha="2026-10-01T10:00:00Z"),  # fuera de ventana
        _commit("d" * 40, "feat: después del corte", [], fecha="2026-10-20T10:00:00Z"),          # posterior
    ]
    r5 = [a for a in evaluar_reglas(commits, CORTE) if a["regla"] == "R5"]

    assert [a["evidencia_ids"] for a in r5] == [["a" * 40]]
    assert r5[0]["fuente"] == "github" and "dice agregar pruebas" in r5[0]["motivo"]


def test_dataset_sin_detalle_no_cambia_las_alertas_de_ta017():
    """Las evidencias del dataset no traen archivos: R5 no aparece y R1–R4 siguen igual."""
    from app.modulos.evidencias.dataset import cargar_evidencias
    reglas = {a["regla"] for a in evaluar_reglas(cargar_evidencias(), CORTE)}
    assert "R5" not in reglas


# -- explicación ---------------------------------------------------------------

def test_plantilla_incluye_el_motivo_y_no_acusa():
    alerta = {"regla": "R5", "fuente": "github", "evidencia_ids": ["a" * 40],
              "explicacion": None, "origen_explicacion": None,
              "motivo": "El mensaje «test: x» dice agregar pruebas, pero no se modificó ningún archivo de pruebas."}
    texto = GeneradorExplicacionPlantilla().generar(alerta, CORTE)["texto"]

    assert texto.startswith("Regla R5:")
    assert alerta["motivo"] in texto
    assert "no asigna nota" in texto


def test_el_prompt_de_gemini_lleva_el_motivo_como_reason():
    alerta = {"regla": "R5", "fuente": "github", "evidencia_ids": ["a" * 40],
              "explicacion": None, "origen_explicacion": None, "motivo": "Motivo calculado."}
    prompt = build_batch_prompt([alerta], CORTE)
    assert '"reason": "Motivo calculado."' in prompt
    assert "do not claim the student lied" in prompt


def test_el_grafo_garantiza_el_motivo_y_lo_envia_sin_nombres_a_gemini():
    from app.modulos.supervision.grafo.supervisor import build_supervisor_graph, build_supervisor_input

    class Fuente:
        def __init__(self, evidencias):
            self.evidencias = evidencias

        def obtener_evidencias(self, referencia, proyecto_id, **_):
            return self.evidencias

    class GeminiQueResume:
        """Simula a Gemini: responde sin repetir el motivo."""
        prompts = []

        def generar_lote(self, alertas, fecha_corte, contextos=None):
            self.prompts.append([a.get("motivo") for a in alertas])
            return [{"texto": "Conviene revisar el commit.", "origen": "gemini"} for _ in alertas]

    commit = _commit("a" * 40, "test: pruebas de Ana Torres", ["README.md"])
    gemini = GeminiQueResume()
    graph = build_supervisor_graph({"github": Fuente([commit])}, explainer=gemini)
    final = graph.invoke(build_supervisor_input(1, CORTE, {"github": "org/repo"}))

    r5 = [a for a in final["alertas"] if a["regla"] == "R5"][0]
    assert r5["explicacion"].startswith(r5["motivo"])           # el motivo siempre se ve
    assert r5["explicacion"].endswith("Conviene revisar el commit.")
    assert "Ana Torres" not in str(gemini.prompts)                 # a Gemini va seudonimizado


# -- adaptador de GitHub ---------------------------------------------------------

def test_cliente_lee_archivos_lineas_y_merge(monkeypatch):
    respuesta = {"stats": {"additions": 7, "deletions": 2}, "parents": [{}, {}],
                 "files": [{"filename": "a.py"}, {"filename": "docs/b.md"}]}
    monkeypatch.setattr(GitHubClient, "_get", lambda self, ruta, params=None: (respuesta, {}))

    detalle = GitHubClient(token="x").detalle_commit("org/repo", "a" * 40)

    assert detalle == {"archivos": ["a.py", "docs/b.md"], "adiciones": 7, "eliminaciones": 2, "es_merge": True}


def test_adaptador_agrega_el_detalle_y_tolera_que_falle(monkeypatch):
    monkeypatch.setenv("GITHUB_DETALLE_COMMITS", "1")
    monkeypatch.setattr(adaptador, "cargar_env", lambda: {})
    crudos = [{"sha": "a" * 40, "mensaje": "feat: x", "autor": "u", "fecha": "2026-10-12T10:00:00Z"},
              {"sha": "b" * 40, "mensaje": "feat: y", "autor": "u", "fecha": "2026-10-12T11:00:00Z"}]
    monkeypatch.setattr(GitHubClient, "commits_detallados", lambda self, repo, desde=None, maximo=None: crudos)

    def detalle(self, repo, sha):
        if sha.startswith("b"):
            raise GitHubError("HTTP 502")
        return {"archivos": ["x.py"], "adiciones": 1, "eliminaciones": 0, "es_merge": False}

    monkeypatch.setattr(GitHubClient, "detalle_commit", detalle)
    evidencias = adaptador.FuenteEvidenciaGitHub().obtener_evidencias("org/repo", 1)

    assert evidencias[0].archivos == ["x.py"]
    assert evidencias[1].archivos is None  # sin detalle: sigue siendo evidencia, R5 lo omite


def test_detalle_se_puede_apagar(monkeypatch):
    monkeypatch.setenv("GITHUB_DETALLE_COMMITS", "0")
    monkeypatch.setattr(adaptador, "cargar_env", lambda: {})
    monkeypatch.setattr(GitHubClient, "commits_detallados", lambda self, repo, desde=None, maximo=None:
                        [{"sha": "a" * 40, "mensaje": "m", "autor": "u", "fecha": None}])
    monkeypatch.setattr(GitHubClient, "detalle_commit", lambda *a: pytest.fail("no debe consultarse"))

    assert adaptador.FuenteEvidenciaGitHub().obtener_evidencias("org/repo", 1)[0].archivos is None


# -- PostgreSQL: la alerta R5 se guarda y se consulta con su motivo -----------

def test_r5_se_guarda_y_se_consulta_con_su_motivo():
    import os
    from datetime import date

    url = os.getenv("DATABASE_URL", "")
    if not url:
        pytest.skip("Falta DATABASE_URL.")
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from app.compartido import modelos_orm as orm
    from app.modulos.supervision.adaptadores.plantilla import GeneradorExplicacionPlantilla
    from app.modulos.supervision.adaptadores.sql import SqlSupervisionRepository
    from app.modulos.supervision.service import SupervisionService

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1 from alerta limit 1"))
    except Exception as error:
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(error).__name__}")

    class Fuente:
        def __init__(self, evidencias):
            self.evidencias = evidencias

        def obtener_evidencias(self, referencia, proyecto_id, **_):
            for e in self.evidencias:
                e.proyecto_id = proyecto_id
            return self.evidencias

    refs = {"github": "octocat/Hello-World", "notion": "base-r5"}
    with Session(engine) as s:
        docente = orm.Docente(nombre="Docente R5", correo="r5@prueba.test", password_hash="x")
        s.add(docente)
        s.flush()
        proyecto = orm.Proyecto(docente_id=docente.id, nombre="Proyecto R5", curso="TI1",
                                fecha_inicio=date(2026, 9, 21), fecha_fin=date(2026, 11, 30),
                                url_publica="https://demo.test", elemento_verificar="h1")
        s.add(proyecto)
        s.flush()
        for tipo, ref in refs.items():
            s.add(orm.Fuente(proyecto_id=proyecto.id, tipo=tipo, referencia=ref))
        s.commit()
        pid, did = proyecto.id, docente.id

    try:
        with Session(engine) as s:
            fuentes = {"github": Fuente([_commit("a" * 40, "test: pruebas del login", ["README.md"])]),
                       "notion": Fuente([])}
            servicio = SupervisionService(SqlSupervisionRepository(s), fuentes, GeneradorExplicacionPlantilla())
            servicio.run_cutoff(pid, refs, CORTE)
            alertas = servicio.alerts(pid, "2026-10-12")["alertas"]

        r5 = [a for a in alertas if a["regla"] == "R5"]
        assert len(r5) == 1
        assert "dice agregar pruebas" in r5[0]["explicacion"]
        assert r5[0]["evidencia"]["id_externo"] == "a" * 40
    finally:
        with Session(engine) as s:
            s.execute(orm.Alerta.__table__.delete().where(orm.Alerta.proyecto_id == pid))
            s.delete(s.get(orm.Proyecto, pid))
            s.flush()
            s.delete(s.get(orm.Docente, did))
            s.commit()
