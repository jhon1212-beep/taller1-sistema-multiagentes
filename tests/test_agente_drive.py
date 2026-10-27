# -*- coding: utf-8 -*-
"""TA-014: pruebas del adaptador y del agente Drive (sin red)."""
from app.modulos.evidencias.adaptadores.drive import adaptador
from app.modulos.evidencias.adaptadores.drive.cliente import DriveClient, DriveError
from app.modulos.evidencias.agentes.agente_drive import agente_drive

ARCHIVO = {
    "id": "1AbCdEfG",
    "nombre": "Plan de pruebas Sprint 1.pdf",
    "tipo": "application/pdf",
    "fecha": "2026-09-30T16:30:00Z",
    "editor": "Jhon Chavez",
}


def test_normalizar_archivo_mapea_los_campos():
    e = adaptador._normalizar_archivo(ARCHIVO, 1)
    assert e.fuente == "drive"
    assert e.id_externo == "1AbCdEfG"
    assert e.autor == "Jhon Chavez"
    assert e.fecha == ARCHIVO["fecha"]
    assert e.descripcion == ARCHIVO["nombre"]
    assert e.tipo_archivo == "application/pdf"
    assert e.proyecto_id == 1


def test_normalizar_archivo_usa_desconocido_si_falta_el_editor():
    e = adaptador._normalizar_archivo({**ARCHIVO, "editor": None}, 1)
    assert e.autor == "desconocido"


def test_agente_drive_devuelve_los_10_archivos(monkeypatch):
    llamadas = {}

    def falso(self, carpeta_id, maximo=None):
        llamadas["carpeta"] = carpeta_id
        return [dict(ARCHIVO, id=f"id-{i}") for i in range(10)]

    monkeypatch.setattr(DriveClient, "archivos_de_carpeta", falso)

    estado = agente_drive({"carpeta_id": "carpeta-demo", "proyecto_id": 1})

    assert llamadas["carpeta"] == "carpeta-demo"
    assert len(estado["evidencias"]) == 10
    assert all(e["fuente"] == "drive" for e in estado["evidencias"])
    assert estado["estado_fuente"] == "ok"
    assert estado["error"] is None


def test_agente_drive_devuelve_error_si_la_api_falla(monkeypatch):
    def falla(self, carpeta_id, maximo=None):
        raise DriveError("HTTP 403 al consultar la carpeta de Drive")

    monkeypatch.setattr(DriveClient, "archivos_de_carpeta", falla)

    estado = agente_drive({"carpeta_id": "x", "proyecto_id": 1})

    assert estado["evidencias"] == []
    assert estado["estado_fuente"] == "fallo"
    assert "403" in estado["error"]