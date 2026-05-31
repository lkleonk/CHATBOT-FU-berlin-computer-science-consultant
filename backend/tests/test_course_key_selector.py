from app.services.nodes.course_key_selector import _sanitize_selector_result, heuristic_select_course_keys


def test_heuristic_selector_expands_swp_question_across_areas():
    result = heuristic_select_course_keys("Welche Softwareprojekte gibt es im SoSe 2026?")

    assert result["needs_clarification"] is False
    assert result["keys"] == [
        "sose26/technical/swp",
        "sose26/practical/swp",
        "sose26/theoretical/swp",
    ]


def test_heuristic_selector_expands_area_question_across_types():
    result = heuristic_select_course_keys("technical courses in sose26")

    assert result["keys"] == [
        "sose26/technical/vl",
        "sose26/technical/swp",
        "sose26/technical/seminar",
    ]


def test_heuristic_selector_skips_pure_rule_question():
    result = heuristic_select_course_keys("Wie viele LP brauche ich im Anwendungsbereich?")

    assert result["needs_clarification"] is False
    assert result["keys"] == []


def test_heuristic_selector_skips_software_project_count_rule_question():
    result = heuristic_select_course_keys("How many Softwareprojekte can I take in SoSe 2026?")

    assert result["needs_clarification"] is False
    assert result["keys"] == []


def test_heuristic_selector_still_handles_offered_count_question():
    result = heuristic_select_course_keys("How many Softwareprojekte are offered in SoSe 2026?")

    assert result["needs_clarification"] is False
    assert result["keys"] == [
        "sose26/technical/swp",
        "sose26/practical/swp",
        "sose26/theoretical/swp",
    ]


def test_sanitizer_drops_llm_keys_for_degree_rule_question():
    result = _sanitize_selector_result(
        {
            "keys": ["sose26/technical/swp", "sose26/practical/swp"],
            "needs_clarification": False,
            "clarification_question": "",
        },
        "How many Softwareprojekte can I take?",
    )

    assert result["course_lookup_keys"] == []
    assert result["course_lookup_needs_clarification"] is False


def test_heuristic_selector_asks_for_semester_on_offering_question():
    result = heuristic_select_course_keys("Welche Softwareprojekte gibt es?")

    assert result["needs_clarification"] is True
    assert result["keys"] == []
