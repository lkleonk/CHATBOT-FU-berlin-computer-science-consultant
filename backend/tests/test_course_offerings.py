from app.domain.course_offerings import (
    build_available_semesters_note,
    build_course_citations,
    build_course_lookup_tree,
    format_course_lookup_context,
    get_course_bucket,
    iter_lookup_keys,
    load_course_offerings,
    normalize_course_url,
)


def test_course_offerings_loads_path_like_lookup_keys():
    offerings = load_course_offerings()

    keys = iter_lookup_keys(offerings)

    assert "sose26/technical/swp" in keys
    assert "sose26/practical/seminar" in keys
    assert all("::" not in key for key in keys)


def test_available_semesters_note_is_derived_from_offerings():
    note = build_available_semesters_note()

    assert "sose26" in note
    assert "No local course-offering data exists for other semesters." in note


def test_course_lookup_tree_shows_bucket_keys_and_examples():
    tree = build_course_lookup_tree()

    assert "sose26" in tree
    assert "swp -> sose26/technical/swp" in tree
    assert "Softwareprojekt: Telematik" in tree


def test_course_lookup_context_contains_whole_bucket():
    bucket = get_course_bucket("sose26/technical/swp")

    context = format_course_lookup_context([bucket])

    assert "## sose26/technical/swp" in context
    assert "Softwareprojekt: Telematik" in context
    assert "Softwareprojekt A is graded and Softwareprojekt B is ungraded" in context


def test_markdown_style_urls_are_normalized_for_citations():
    assert (
        normalize_course_url("[https://example.test/course](https://example.test/course)")
        == "https://example.test/course"
    )

    bucket = get_course_bucket("sose26/practical/vl")
    citations = build_course_citations([bucket])

    assert any(citation["source"].startswith("https://") for citation in citations)
    assert all(not citation["source"].startswith("[") for citation in citations)
