"""TA-023: comprueba la sustitución de nombres antes de Gemini."""
from app.modulos.evidencias.dominio import Evidencia, EvidenciaNotion
from app.modulos.supervision.pseudonymizer import GENERIC_NAME, NO_AUTHOR, Pseudonymizer


def commit(author, message, id_="sha-1"):
    return Evidencia("github", id_, author, "2026-10-10T10:00:00Z", message, 1)


def test_aliases_are_stable_and_follow_order_of_appearance():
    p = Pseudonymizer(["Elena Ríos", "Carlos León", "elena ríos"])
    assert p.alias("Elena Ríos") == "Member 1"
    assert p.alias("ELENA RÍOS") == "Member 1"
    assert p.alias("Carlos León") == "Member 2"


def test_unknown_or_missing_author_never_returns_a_name():
    p = Pseudonymizer(["Elena Ríos"])
    assert p.alias(None) == NO_AUTHOR
    assert p.alias("") == NO_AUTHOR
    assert p.alias("External Person") == GENERIC_NAME


def test_scrub_replaces_full_names_and_single_name_parts():
    p = Pseudonymizer(["Elena Ríos", "Carlos León"])
    result = p.scrub("Revisión de Elena Ríos con Carlos; falta que León apruebe")
    assert "Elena" not in result and "Ríos" not in result
    assert "Carlos" not in result and "León" not in result
    assert result == "Revisión de Member 1 con Member 2; falta que Member 2 apruebe"


def test_scrub_does_not_touch_words_that_only_contain_a_name():
    p = Pseudonymizer(["Ana Torres"])
    assert p.scrub("Análisis de datos") == "Análisis de datos"


def test_shared_name_part_uses_a_generic_marker():
    p = Pseudonymizer(["Jhon Chávez", "Jhon Castro"])
    assert p.scrub("Jhon subió el informe") == f"{GENERIC_NAME} subió el informe"


def test_alert_context_contains_only_safe_fields_of_its_evidence():
    evidences = [
        EvidenciaNotion(
            "notion", "t1", "Elena Ríos", "2026-10-01T10:00:00Z",
            "Tarea de Elena Ríos", 1, estado="En curso", fecha_limite="2026-10-05"
        ),
        commit("Carlos León", "commit de Carlos", "sha-9"),
    ]
    p = Pseudonymizer.from_evidences(evidences)
    alert = {"regla": "R1", "fuente": "notion", "evidencia_ids": ["t1"]}
    context = p.alert_context(alert, evidences)
    assert context == [{
        "fuente": "notion", "id_externo": "t1",
        "fecha": "2026-10-01T10:00:00Z", "estado": "En curso",
        "fecha_limite": "2026-10-05", "autor": "Member 1",
        "descripcion": "Tarea de Member 1",
    }]
    assert "Carlos" not in str(context)
