import json
from pathlib import Path

import pytest

from app.domain.course_offerings import (
    build_available_semesters_note,
    build_course_citations,
    build_course_lookup_tree,
    format_course_lookup_context,
    get_course_bucket,
    has_offerings,
    iter_lookup_keys,
    load_course_entries,
    normalize_course_url,
    project_offerings,
    validate_course_entries,
)


MSC = "msc_informatik"
FIXTURE_PATH = Path(__file__).with_name("fixtures") / "msc_informatik_buckets_pre_migration.json"


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
    assert (
        normalize_course_url("[https://example.test/course](https://example.test/course)")
        == "https://example.test/course"
    )

    bucket = get_course_bucket(MSC, "sose26/practical/vl")
    citations = build_course_citations([bucket])

    assert any(citation["source"].startswith("https://") for citation in citations)
    assert all(not citation["source"].startswith("[") for citation in citations)


def test_degree_without_tagged_entries_has_no_offerings():
    assert has_offerings(MSC)
    assert not has_offerings("msc_data_science")
    assert project_offerings("msc_data_science") == {}
    assert "none" in build_available_semesters_note("msc_data_science")


def test_projection_matches_pre_migration_master_buckets():
    """Gate for the flat-format migration: the projected msc_informatik tree
    must contain exactly the buckets and courses of the old bucket-tree file."""
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
        assert sorted(map(comparable, old_courses)) == sorted(
            map(comparable, new_buckets[key])
        ), f"bucket {key} diverged"


def _base_entry(**overrides):
    entry = {
        "semester": "sose26",
        "type": "vl",
        "title": "Telematik",
        "lp": 10,
        "schedule": None,
        "description": None,
        "url": None,
        "degrees": {
            "msc_informatik": [{"area": "technical", "module_catalog_name": "Telematik"}],
        },
    }
    entry.update(overrides)
    return entry


def test_validation_accepts_shared_entry_with_lp_override_and_module_ids():
    entry = _base_entry(
        degrees={
            "msc_informatik": [{"area": "technical", "module_catalog_name": "Telematik"}],
            "msc_data_science": {"area": "technologies", "module_id": "telematik", "lp": 8},
        }
    )

    validate_course_entries([entry])

    tree = _project([entry], "msc_data_science")
    course = tree["sose26"]["technologies"]["vl"][0]
    assert course["lp"] == 8
    assert course["module_ids"] == ["telematik"]
    assert course["module_catalog_name"] == "Telematik"


def test_validation_rejects_unknown_degree_area_and_module_id():
    with pytest.raises(ValueError, match="unknown degree id"):
        validate_course_entries([_base_entry(degrees={"bsc_astrology": {"area": "pflicht"}})])

    with pytest.raises(ValueError, match="area vocabulary"):
        validate_course_entries(
            [_base_entry(degrees={"msc_informatik": {"area": "grundlagen", "module_catalog_name": "X"}})]
        )

    with pytest.raises(ValueError, match="unknown module ids"):
        validate_course_entries(
            [_base_entry(degrees={"msc_data_science": {"area": "technologies", "module_id": "telematix"}})]
        )


def test_validation_enforces_module_id_policy_per_degree():
    # Canonical-list degree without module ids -> rejected.
    with pytest.raises(ValueError, match="requires module_ids"):
        validate_course_entries(
            [_base_entry(degrees={"msc_data_science": {"area": "technologies"}})]
        )

    # Degree without canonical list must not carry module ids.
    with pytest.raises(ValueError, match="no canonical module list"):
        validate_course_entries(
            [
                _base_entry(
                    degrees={
                        "msc_informatik": {
                            "area": "technical",
                            "module_catalog_name": "Telematik",
                            "module_id": "telematik",
                        }
                    }
                )
            ]
        )

    # Degree without canonical list requires module_catalog_name.
    with pytest.raises(ValueError, match="module_catalog_name"):
        validate_course_entries([_base_entry(degrees={"msc_informatik": {"area": "technical"}})])


def test_validation_rejects_duplicate_course_entries():
    with pytest.raises(ValueError, match="duplicates"):
        validate_course_entries([_base_entry(), _base_entry()])


def test_module_ids_shorthand_and_list_are_equivalent():
    single = _base_entry(
        title="Softwareprojekt: Telematik",
        type="swp",
        degrees={
            "msc_data_science": {
                "area": "technologies",
                "module_ids": ["softwareprojekt_data_science_a", "softwareprojekt_data_science_b"],
            }
        },
    )

    validate_course_entries([single])

    course = _project([single], "msc_data_science")["sose26"]["technologies"]["swp"][0]
    assert course["module_ids"] == [
        "softwareprojekt_data_science_a",
        "softwareprojekt_data_science_b",
    ]
    assert "Softwareprojekt Data Science A" in course["module_catalog_name"]
    assert "Softwareprojekt Data Science B" in course["module_catalog_name"]


def test_bachelor_module_flag_is_projected_and_rendered():
    entry = _base_entry(
        title="Betriebs- und Kommunikationssysteme",
        degrees={
            "msc_informatik": {
                "area": "technical",
                "module_catalog_name": "Betriebs- und Kommunikationssysteme",
                "is_bachelor_module": True,
            }
        },
    )

    validate_course_entries([entry])

    course = _project([entry], MSC)["sose26"]["technical"]["vl"][0]
    assert course["is_bachelor_module"] is True

    context = format_course_lookup_context(
        [
            {
                "key": "sose26/technical/vl",
                "semester": "sose26",
                "area": "technical",
                "course_type": "vl",
                "courses": [course],
            }
        ]
    )
    assert "maximum of 15 LP of Bachelor modules" in context


def _project(entries, degree_id):
    """Project ad-hoc entries without touching the module-level caches."""
    from unittest.mock import patch

    from app.domain import course_offerings

    course_offerings._project_offerings_cached.cache_clear()
    try:
        with patch.object(course_offerings, "load_course_entries", return_value=entries):
            return course_offerings.project_offerings(degree_id)
    finally:
        course_offerings._project_offerings_cached.cache_clear()


def test_real_data_file_is_valid():
    validate_course_entries(load_course_entries())
