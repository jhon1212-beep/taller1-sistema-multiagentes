import pytest
from pydantic import ValidationError

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.evidencias.esquema import EvidenciaNormalizada
from app.modulos.evidencias.normalizacion import normalizar

BASE = dict(fuente="github", id_externo="a" * 40, autor="chavez",
            fecha="2026-10-01T10:00:00Z", descripcion="TA-010: prueba", proyecto_id=1)


def test_esquema_acepta_los_seis_campos():
    e = EvidenciaNormalizada(**BASE)
    assert e.fecha.tzinfo is not None


@pytest.mark.parametrize("campo", ["id_externo", "autor", "descripcion"])
def test_esquema_rechaza_campos_vacios(campo):
    with pytest.raises(ValidationError):
        EvidenciaNormalizada(**{**BASE, campo: "  "})


def test_esquema_rechaza_fecha_sin_zona_y_fuente_invalida():
    with pytest.raises(ValidationError):
        EvidenciaNormalizada(**{**BASE, "fecha": "2026-10-01T10:00:00"})
    with pytest.raises(ValidationError):
        EvidenciaNormalizada(**{**BASE, "fuente": "jira"})


def test_normalizar_commits_y_tareas_sin_responsable():
    commit = Evidencia(**BASE)
    tarea = Evidencia(fuente="notion", id_externo="pagina-1", autor="",
                      fecha="2026-10-02T09:00:00Z", descripcion="Tarea sin dueño", proyecto_id=1)
    resultado = normalizar([commit, tarea])
    assert [e.fuente for e in resultado] == ["github", "notion"]
    assert resultado[1].autor == "sin responsable"


def test_normalizar_falla_si_falta_la_fecha():
    sin_fecha = Evidencia(**{**BASE, "fecha": None})
    with pytest.raises(ValidationError):
        normalizar([sin_fecha])