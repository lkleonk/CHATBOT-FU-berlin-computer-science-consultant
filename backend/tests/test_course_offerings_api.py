from fastapi.testclient import TestClient

from app.main import app


def _all_courses(body):
    return [
        course
        for semester in body["semesters"]
        for area in semester["areas"]
        for course_type in area["course_types"]
        for course in course_type["courses"]
    ]


def test_course_offerings_endpoint_returns_default_degree_projection():
    response = TestClient(app).get("/api/course-offerings")

    assert response.status_code == 200
    body = response.json()
    assert body["degree_program"] == "M.Sc. Informatik"
    assert body["semesters"][0]["id"] == "sose26"
    assert body["semesters"][0]["label"] == "SoSe 2026"

    technical = next(area for area in body["semesters"][0]["areas"] if area["id"] == "technical")
    assert technical["label"] == "Technical Informatics"
    lecture = next(course_type for course_type in technical["course_types"] if course_type["id"] == "vl")
    assert lecture["label"] == "Lecture"


def test_course_offerings_endpoint_normalizes_urls_and_preserves_null_lp():
    response = TestClient(app).get("/api/course-offerings")

    courses = _all_courses(response.json())
    cluster_computing = next(course for course in courses if course["title"] == "Cluster Computing")
    assert cluster_computing["lp"] is None
    assert cluster_computing["url"].startswith("https://")
    assert not cluster_computing["url"].startswith("[")


def test_course_offerings_endpoint_is_degree_scoped_and_read_only(monkeypatch):
    def unexpected_user_action(*args, **kwargs):
        raise AssertionError("Read-only course offerings must not consume user quota.")

    def unexpected_session_access(*args, **kwargs):
        raise AssertionError("Read-only course offerings must not initialise sessions.")

    monkeypatch.setattr("app.routes.daily_quota.consume_user_action", unexpected_user_action)
    monkeypatch.setattr("app.routes.get_session_service", unexpected_session_access)

    response = TestClient(app).get("/api/course-offerings", params={"degree": "msc_data_science"})

    assert response.status_code == 200
    body = response.json()
    assert body["degree_program"] == "M.Sc. Data Science"
    assert body["semesters"][0]["id"] == "sose26"
    assert {area["id"] for area in body["semesters"][0]["areas"]} == {"grundlagen", "life_sciences", "technologies"}


def test_course_offerings_endpoint_rejects_unknown_degree():
    response = TestClient(app).get("/api/course-offerings", params={"degree": "bsc_astrology"})

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "unknown_degree"


def test_course_offerings_endpoint_returns_bsc_sose26_projection():
    response = TestClient(app).get("/api/course-offerings", params={"degree": "bsc_informatik"})

    assert response.status_code == 200
    body = response.json()
    assert body["degree_program"] == "B.Sc. Informatik"
    assert body["semesters"][0]["id"] == "sose26"
    assert any(area["id"] == "compulsory" for area in body["semesters"][0]["areas"])
    compulsory = next(area for area in body["semesters"][0]["areas"] if area["id"] == "compulsory")
    practical = next(course_type for course_type in compulsory["course_types"] if course_type["id"] == "praktikum")
    assert practical["label"] == "Practical course"
