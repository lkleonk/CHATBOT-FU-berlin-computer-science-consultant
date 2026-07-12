import pytest
from fastapi.testclient import TestClient

from app.domain.degrees import (
    DEFAULT_DEGREE_ID,
    get_degree,
    get_degree_or_default,
    is_valid_degree,
    list_degrees,
)
from app.main import app


def test_registry_contains_known_degrees():
    degree_ids = {degree.id for degree in list_degrees()}
    assert {"msc_informatik", "msc_data_science"} <= degree_ids
    assert DEFAULT_DEGREE_ID == "msc_informatik"


def test_get_degree_rejects_unknown_id():
    with pytest.raises(ValueError):
        get_degree("bsc_astrology")
    assert not is_valid_degree("bsc_astrology")


def test_get_degree_or_default_falls_back():
    assert get_degree_or_default(None).id == DEFAULT_DEGREE_ID
    assert get_degree_or_default("bsc_astrology").id == DEFAULT_DEGREE_ID
    assert get_degree_or_default("msc_informatik").id == "msc_informatik"


def test_degree_definitions_are_complete():
    for degree in list_degrees():
        prompts = degree.prompts

        assert degree.display_name
        assert degree.get_program_rules().sections
        assert callable(degree.validate_study_plan)
        assert callable(degree.enrich_study_plan)
        assert degree.study_plan_schema.get("type") == "object"
        for prompt_text in (
            prompts.domain_scope,
            prompts.answer_identity,
            prompts.classifier_system_prompt,
            prompts.course_key_selector_template,
            prompts.study_plan_parser_system_prompt,
            prompts.answer_composer_system_prompt,
            prompts.offtopic_reply_de,
            prompts.offtopic_reply_en,
        ):
            assert prompt_text.strip()


def test_data_science_program_rules_endpoint():
    response = TestClient(app).get("/api/program-rules", params={"degree": "msc_data_science"})

    assert response.status_code == 200
    body = response.json()
    assert body["degree_program"] == "FU Berlin M.Sc. Data Science"
    assert {section["id"] for section in body["sections"]} >= {
        "overall-structure",
        "grundlagenbereich",
        "profile-life-sciences",
        "profile-technologies",
    }


def test_degrees_endpoint_lists_known_degrees():
    response = TestClient(app).get("/api/degrees")

    assert response.status_code == 200
    body = response.json()
    assert {entry["id"] for entry in body} == {degree.id for degree in list_degrees()}
    assert all(entry["display_name"] for entry in body)


def test_program_rules_endpoint_rejects_unknown_degree():
    response = TestClient(app).get("/api/program-rules", params={"degree": "bsc_astrology"})

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "unknown_degree"


def test_create_session_rejects_unknown_degree():
    response = TestClient(app).post("/api/sessions", json={"degree": "bsc_astrology"})

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "unknown_degree"


def test_create_session_returns_degree():
    client = TestClient(app)

    default_response = client.post("/api/sessions")
    explicit_response = client.post("/api/sessions", json={"degree": "msc_informatik"})

    assert default_response.status_code == 200
    assert default_response.json()["degree"] == DEFAULT_DEGREE_ID
    assert explicit_response.status_code == 200
    assert explicit_response.json()["degree"] == "msc_informatik"
