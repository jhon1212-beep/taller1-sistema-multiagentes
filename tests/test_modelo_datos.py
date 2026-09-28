from app.models import Base

TABLAS = {
    "docente", "proyecto", "integrante", "fuente",
    "evidencia", "indicador", "alerta", "validacion",
}

# (tabla hija, tabla padre) de cada relación del diagrama ER
RELACIONES = {
    ("proyecto", "docente"),
    ("integrante", "proyecto"),
    ("fuente", "proyecto"),
    ("evidencia", "proyecto"),
    ("evidencia", "fuente"),
    ("indicador", "proyecto"),
    ("alerta", "proyecto"),
    ("alerta", "evidencia"),
    ("validacion", "proyecto"),
}


def test_el_modelo_tiene_las_8_tablas():
    assert set(Base.metadata.tables) == TABLAS


def test_relaciones_del_diagrama_er():
    encontradas = {
        (tabla.name, fk.column.table.name)
        for tabla in Base.metadata.tables.values()
        for fk in tabla.foreign_keys
    }
    assert encontradas == RELACIONES
