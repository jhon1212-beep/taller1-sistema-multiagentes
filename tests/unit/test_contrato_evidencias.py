from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa

REFERENCIA = "https://github.com/jhon1212-beep/taller1-sistema-multiagentes"


def test_fuente_falsa_devuelve_evidencias_del_proyecto_pedido():
    evidencias = FuenteEvidenciaFalsa().obtener_evidencias(REFERENCIA, proyecto_id=1)

    assert [e.fuente for e in evidencias] == ["github", "notion", "drive"]
    assert all(e.proyecto_id == 1 for e in evidencias)


def test_fuente_falsa_respeta_el_limite():
    evidencias = FuenteEvidenciaFalsa().obtener_evidencias(
        REFERENCIA, proyecto_id=1, limite=2
    )

    assert len(evidencias) == 2


def test_fuente_falsa_no_devuelve_evidencias_de_otro_proyecto():
    assert FuenteEvidenciaFalsa().obtener_evidencias(REFERENCIA, proyecto_id=999) == []


def test_evidencia_se_serializa_a_diccionario():
    evidencia = FuenteEvidenciaFalsa().obtener_evidencias(REFERENCIA, proyecto_id=1)[0]

    assert evidencia.to_dict() == {
        "fuente": "github",
        "id_externo": "e3a1c9f2b7d4a0158e6f2c9b1d7a4e8f3c2b1a90",
        "autor": "jhon1212-beep",
        "fecha": "2026-09-28T14:02:11Z",
        "descripcion": "TA-001: repositorio y entorno base",
        "proyecto_id": 1,
    }