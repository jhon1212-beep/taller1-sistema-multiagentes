"""TA-010: obtiene 5 commits y 5 tareas, los normaliza y los guarda en PostgreSQL."""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from datetime import date  # noqa: E402

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.compartido.db import obtener_engine  # noqa: E402
from app.compartido.modelos_orm import Docente, Fuente, Proyecto  # noqa: E402
from app.modulos.evidencias.adaptadores.github.adaptador import FuenteEvidenciaGitHub  # noqa: E402
from app.modulos.evidencias.adaptadores.postgres.repositorio import RepositorioEvidenciasSQL  # noqa: E402
from app.modulos.evidencias.normalizacion import normalizar  # noqa: E402

# AJUSTA este import al nombre real de tu adaptador de TA-007:
from app.modulos.evidencias.adaptadores.notion.adaptador import FuenteEvidenciaNotion  # noqa: E402

REPO = "jhon1212-beep/taller1-sistema-multiagentes"
NOTION_DB = os.environ["NOTION_DATABASE_ID"]

def preparar_proyecto(s: Session) -> int:
    proyecto = s.scalar(select(Proyecto).where(Proyecto.nombre == "Proyecto demo TA-010"))
    if proyecto is None:
        docente = Docente(nombre="Docente demo", correo="docente.demo@example.com",
                          password_hash="no-usado-en-ta010")
        s.add(docente); s.flush()
        proyecto = Proyecto(docente_id=docente.id, nombre="Proyecto demo TA-010",
                            curso="Taller Integrador 1", fecha_inicio=date(2026, 9, 28),
                            fecha_fin=date(2026, 12, 31), url_publica="https://example.com",
                            elemento_verificar="demo")
        s.add(proyecto); s.flush()
    for tipo, ref in (("github", REPO), ("notion", NOTION_DB)):
        fuente = s.scalar(
            select(Fuente).where(Fuente.proyecto_id == proyecto.id, Fuente.tipo == tipo)
        )
        if fuente is None:
            s.add(Fuente(proyecto_id=proyecto.id, tipo=tipo, referencia=ref))
        else:
            fuente.referencia = ref  # corrige la referencia de la corrida anterior
    s.commit()
    return proyecto.id


with Session(obtener_engine()) as sesion:
    pid = preparar_proyecto(sesion)
    commits = FuenteEvidenciaGitHub().obtener_evidencias(REPO, pid, limite=5)
    tareas = FuenteEvidenciaNotion().obtener_evidencias(NOTION_DB, pid, limite=5)  # ajusta si tu firma difiere
    normalizadas = normalizar(commits + tareas)
    repo = RepositorioEvidenciasSQL(sesion)
    print(f"Guardadas: {repo.guardar(normalizadas)}")
    for e in repo.listar(pid):
        print(e.fuente, e.id_externo[:12], e.autor, e.fecha.isoformat(), e.descripcion[:40])