import json
from pathlib import Path

from app.domain.catalog_data import COURSES_PATH, COURSE_OFFERINGS_DIR, DEGREE_MODULES_DIR, load_courses
from app.domain.course_offerings import (
    build_available_semesters_note,
    build_course_citations,
    build_course_lookup_tree,
    format_course_lookup_context,
    get_course_bucket,
    has_offerings,
    iter_lookup_keys,
    normalize_course_url,
    project_offerings,
    validate_course_catalog,
)


MSC = "msc_informatik"
FIXTURE_PATH = Path(__file__).with_name("fixtures") / "msc_informatik_buckets_pre_migration.json"


def test_catalogue_uses_shared_courses_degree_mappings_and_semester_files():
    courses = load_courses()
    info = json.loads((DEGREE_MODULES_DIR / "msc_informatik.json").read_text(encoding="utf-8"))
    sose26 = json.loads((COURSE_OFFERINGS_DIR / "sose26.json").read_text(encoding="utf-8"))

    assert courses["telematik"]["name"] == "Telematik"
    assert any(module["course_id"] == "telematik" for module in info["modules"])
    assert any(offering["course_id"] == "softwareprojekt_telematik" for offering in sose26["offerings"])
    assert COURSES_PATH.exists()


def test_real_catalogue_is_valid():
    validate_course_catalog()


def test_course_offerings_loads_path_like_lookup_keys():
    keys = iter_lookup_keys(MSC)

    assert "sose26/technical/swp" in keys
    assert "sose26/practical/seminar" in keys
    assert all("::" not in key for key in keys)


def test_available_semesters_note_is_derived_from_offerings():
    note = build_available_semesters_note(MSC)

    assert "sose26" in note
    assert "No local course-offering data exists for other semesters." in note


def test_course_lookup_tree_shows_bucket_keys_and_examples():
    tree = build_course_lookup_tree(MSC)

    assert "sose26" in tree
    assert "swp -> sose26/technical/swp" in tree
    assert "Softwareprojekt: Telematik" in tree


def test_course_lookup_context_contains_whole_bucket():
    bucket = get_course_bucket(MSC, "sose26/technical/swp")

    context = format_course_lookup_context([bucket])

    assert "## sose26/technical/swp" in context
    assert "Softwareprojekt: Telematik" in context
    assert "Softwareprojekt A is graded and Softwareprojekt B is ungraded" in context


def test_markdown_style_urls_are_normalized_for_citations():
    assert normalize_course_url("[https://example.test/course](https://example.test/course)") == "https://example.test/course"

    bucket = get_course_bucket(MSC, "sose26/practical/vl")
    citations = build_course_citations([bucket])

    assert any(citation["source"].startswith("https://") for citation in citations)
    assert all(not citation["source"].startswith("[") for citation in citations)
    assert any(citation["source"].endswith("course_offerings/sose26.json") for citation in citations)


def test_data_science_offerings_are_projected():
    assert has_offerings("msc_data_science")
    tree = project_offerings("msc_data_science")
    assert set(tree) == {"sose26"}
    assert set(tree["sose26"]) == {"grundlagen", "life_sciences", "technologies"}

    def titles(area, course_type):
        return {course["title"] for course in tree["sose26"].get(area, {}).get(course_type, [])}

    # Cross-area elective lecture appears in both profile areas.
    assert "Markovketten" in titles("life_sciences", "vl")
    assert "Markovketten" in titles("technologies", "vl")
    # Named Technologies modules land in the technologies area.
    assert "Datenbanksysteme Data Science" in titles("technologies", "vl")
    assert "sose26" in build_available_semesters_note("msc_data_science")


def test_projection_matches_pre_migration_master_buckets():
    old = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    projected = project_offerings(MSC)

    def bucket_index(tree):
        return {
            (semester, area, course_type): courses
            for semester, areas in tree.items()
            for area, course_types in areas.items()
            for course_type, courses in course_types.items()
        }

    old_buckets = bucket_index(old)
    new_buckets = bucket_index(projected)
    assert set(new_buckets) == set(old_buckets)

    def comparable(course):
        return (
            course["title"],
            course["module_catalog_name"],
            course.get("lp"),
            course.get("schedule"),
            course.get("description"),
            course.get("url"),
        )

    for key, old_courses in old_buckets.items():
        assert sorted(map(comparable, old_courses)) == sorted(map(comparable, new_buckets[key])), key
