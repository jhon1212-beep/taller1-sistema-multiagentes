"""TA-015: pruebas unitarias de las funciones del Agente Supervisor."""

import json
from datetime import timezone

import pytest

# Evita ejecutar estas pruebas si LangGraph no está instalado en el entorno.
pytest.importorskip("langgraph")

from app.modulos.evidencias.dominio import Evidencia
from app.modulos.supervision.grafo.supervisor import (
    build_supervisor_input,
    is_within_cutoff,
    merge_dicts,
    parse_cutoff,
    to_consolidated_report,
)


# Fecha de corte base utilizada en las pruebas.
CUTOFF = "2026-10-12T23:59:59-05:00"


def evidence(fecha, fuente="github", id_externo="sha-1"):
    """Crea una evidencia mínima reutilizable para las pruebas."""
    return Evidencia(
        fuente,
        id_externo,
        "autor-demo",
        fecha,
        "Commit demo",
        1,
    )


def test_parse_cutoff_normalizes_to_utc():
    """Verifica que la fecha de corte se normalice correctamente a UTC."""
    parsed = parse_cutoff(CUTOFF)

    assert parsed.tzinfo == timezone.utc
    assert parsed.isoformat() == "2026-10-13T04:59:59+00:00"

    # Ambas fechas representan exactamente el mismo instante.
    assert parse_cutoff("2026-10-13T04:59:59Z") == parsed


@pytest.mark.parametrize(
    "value",
    ["2026-10-12T23:59:59", "12/10/2026", "", None],
)
def test_parse_cutoff_rejects_missing_timezone_or_invalid_format(value):
    """Rechaza fechas sin zona horaria o con formato inválido."""
    with pytest.raises(ValueError):
        parse_cutoff(value)


def test_is_within_cutoff_compares_in_utc_and_keeps_missing_dates():
    """Valida qué evidencias se conservan según la fecha de corte."""
    cutoff = parse_cutoff(CUTOFF)

    # Una evidencia exactamente en el corte debe conservarse.
    assert is_within_cutoff(
        evidence("2026-10-13T04:59:59Z"),
        cutoff,
    )

    # Una evidencia posterior al corte debe descartarse.
    assert not is_within_cutoff(
        evidence("2026-10-13T05:00:00Z"),
        cutoff,
    )

    # Las evidencias sin fecha se conservan según la regla definida en la spec.
    assert is_within_cutoff(evidence(None), cutoff)

    # Una fecha ilegible no se considera válida para el corte.
    assert not is_within_cutoff(
        evidence("fecha-ilegible"),
        cutoff,
    )


def test_merge_dicts_keeps_previous_keys():
    """Comprueba que el reductor combine resultados sin perder claves previas."""
    assert merge_dicts(
        {"github": "ok"},
        {"notion": "fallo"},
    ) == {
        "github": "ok",
        "notion": "fallo",
    }


def test_build_supervisor_input_keeps_ar02_contract_and_only_given_references():
    """Verifica que la entrada inicial respete el contrato AR-02."""
    data = build_supervisor_input(
        1,
        CUTOFF,
        {
            "github": "owner/repo",
            "notion": "",
        },
    )

    # Se mantienen los campos principales definidos por el contrato.
    assert data["proyecto_id"] == 1
    assert data["fecha_corte"] == CUTOFF

    # Solo se guardan referencias que realmente tienen un valor.
    assert data["referencias"] == {
        "github": "owner/repo",
    }

    # Todas las fuentes comienzan en estado pendiente.
    assert data["estado_fuentes"] == {
        "github": "pendiente",
        "notion": "pendiente",
        "drive": "pendiente",
    }

    # TA-015 todavía no calcula los indicadores I1-I4.
    assert data["indicadores"] == {
        "I1": None,
        "I2": None,
        "I3": None,
        "I4": None,
    }


def test_build_supervisor_input_rejects_cutoff_without_timezone():
    """Impide construir la entrada si la fecha de corte no tiene zona horaria."""
    with pytest.raises(ValueError, match="zona horaria"):
        build_supervisor_input(
            1,
            "2026-10-12T23:59:59",
            {"github": "owner/repo"},
        )


def test_consolidated_report_is_json_serializable():
    """Verifica que el resultado consolidado pueda guardarse como JSON."""

    # Estado controlado que simula el resultado final del Supervisor.
    state = {
        "proyecto_id": 1,
        "fecha_corte": CUTOFF,
        "evidencias": [
            evidence("2026-10-01T10:00:00Z"),
        ],
        "estado_fuentes": {
            "github": "ok",
            "notion": "fallo",
            "drive": "ok",
        },
        "errores_fuentes": {
            "github": None,
            "notion": "RuntimeError: caída",
            "drive": None,
        },
        "source_details": {
            "github": {
                "evidencias": 1,
                "fuera_de_corte": 2,
            },
        },
        "indicadores": {
            "I1": None,
            "I2": None,
            "I3": None,
            "I4": None,
        },
        "alertas": [],
    }

    report = to_consolidated_report(state)

    # El reporte debe poder convertirse a JSON sin perder información.
    assert json.loads(json.dumps(report)) == report

    assert report["total_evidencias"] == 1

    # GitHub conserva su resumen de evidencias y elementos fuera de corte.
    assert report["fuentes"]["github"] == {
        "estado": "ok",
        "error": None,
        "evidencias": 1,
        "fuera_de_corte": 2,
    }

    # Notion conserva correctamente su estado de fallo.
    assert report["fuentes"]["notion"]["estado"] == "fallo"

    # Drive no tiene evidencias en este estado controlado.
    assert report["fuentes"]["drive"]["evidencias"] == 0