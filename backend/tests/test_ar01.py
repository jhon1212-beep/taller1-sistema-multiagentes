from app.modulos.evidencias.adaptadores.falso import FuenteEvidenciaFalsa

def test_fuente_falsa_retorna_evidencias():
    fuente = FuenteEvidenciaFalsa()
    evidencias = fuente.obtener_evidencias("https://github.com/jhon1212-beep/taller1-sistema-multiagentes", proyecto_id=1)
    
    assert len(evidencias) == 3
    assert evidencias[0].fuente == "github"
    assert evidencias[1].fuente == "notion"
    assert evidencias[2].fuente == "drive"
    assert evidencias[0].proyecto_id == 1