from fastapi.testclient import TestClient

from app.domain.program_rules import get_program_rules, render_program_rules_context
from app.main import app
from app.prompts import RULES_CONTEXT


def section_by_id(section_id: str):
    catalogue = get_program_rules()
    return next(section for section in catalogue.sections if section.id == section_id)


def test_program_rules_include_softwareprojekt_wahlbereich_caveat():
    section = section_by_id("softwareprojekt")
    text = " ".join(item.text for item in section.items)

    assert "Wahlbereich" in text
    assert "3 Softwareprojekt modules total" in text
    assert "software_project_count" in section.related_issue_codes


def test_program_rules_include_scientific_work_wahlbereich_caveat():
    section = section_by_id("wissenschaftliches-arbeiten")
    text = " ".join(item.text for item in section.items)

    assert "Up to 2 additional Wissenschaftliches Arbeiten modules" in text
    assert "scientific_work_count" in section.related_issue_codes


def test_program_rules_endpoint_returns_catalogue():
    response = TestClient(app).get("/api/program-rules")

    assert response.status_code == 200
    body = response.json()
    assert body["degree_program"] == "FU Berlin Master Informatik"
    assert {section["id"] for section in body["sections"]} >= {
        "overall-structure",
        "informatics-area",
        "softwareprojekt",
        "wissenschaftliches-arbeiten",
    }


def test_rules_context_is_rendered_from_program_rules():
    assert RULES_CONTEXT == render_program_rules_context()


def test_rules_context_includes_softwareprojekt_wahlbereich_caveat():
    assert "At least 1 and at most 2 core Softwareprojekt modules are required." in RULES_CONTEXT
    assert "allowing 3 Softwareprojekt modules total" in RULES_CONTEXT
