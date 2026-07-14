from app.domain.course_offerings import (
    available_semesters,
    build_available_semesters_note,
    get_course_bucket,
    has_offerings,
    iter_lookup_keys,
    project_offerings,
    validate_course_catalog,
)


BSC = "bsc_informatik"


def _courses(tree):
    return [
        course
        for areas in tree.values()
        for course_types in areas.values()
        for courses in course_types.values()
        for course in courses
    ]


def test_bsc_sose26_offerings_are_valid_and_degree_scoped():
    validate_course_catalog()

    assert has_offerings(BSC)
    assert available_semesters(BSC) == ["sose26"]
    assert "No local course-offering data exists for other semesters." in build_available_semesters_note(BSC)


def test_bsc_compulsory_and_elective_modules_project_from_the_shared_semester_file():
    tree = project_offerings(BSC)
    compulsory_lectures = tree["sose26"]["compulsory"]["vl"]
    elective_lectures = tree["sose26"]["compulsory_elective"]["vl"]

    bks = next(course for course in compulsory_lectures if course["title"] == "Betriebs- und Kommunikationssysteme")
    assert bks["lp"] == 6
    assert "19300701" in bks["description"]
    assert "Barry Linnert" in bks["description"]

    assert {course["title"] for course in elective_lectures} >= {
        "Angewandte Biometrie",
        "Architektur eingebetteter Systeme",
        "Funktionale Programmierung",
        "Mensch-Computer Interaktion",
    }


def test_bsc_programmierpraktikum_and_active_scientific_work_choices_are_selectable():
    keys = iter_lookup_keys(BSC)
    assert "sose26/compulsory/praktikum" in keys
    assert "sose26/compulsory/seminar" in keys

    practical = get_course_bucket(BSC, "sose26/compulsory/praktikum")
    assert practical["courses"][0]["title"] == "Programmierpraktikum"
    assert practical["courses"][0]["lp"] == 5

    seminar_titles = {course["title"] for course in get_course_bucket(BSC, "sose26/compulsory/seminar")["courses"]}
    assert "Proseminar: Theoretische Informatik" in seminar_titles
    assert "Seminar/Proseminar: Internet of Things & Security (Technische Informatik)" in seminar_titles
    assert not any("Computer Science Perspectives" in title for title in seminar_titles)
    assert not any("medizinischen Bildverarbeitung" in title for title in seminar_titles)


def test_bsc_math_offerings_are_free_elective_candidates_not_automatic_credit_claims():
    courses = _courses(project_offerings(BSC))
    analysis = next(course for course in courses if course["title"] == "Analysis II")
    computer_math = next(course for course in courses if course["title"] == "Computerorientierte Mathematik II")

    assert analysis["lp"] is None
    assert "candidate" in analysis["description"]
    assert computer_math["lp"] == 5
