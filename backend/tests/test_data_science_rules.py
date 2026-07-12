from app.domain.degrees.msc_data_science.degree_rules import validate_study_plan


GRUNDLAGEN = [
    {"name": "Introduction to Profile Areas", "lp": 5},
    {"name": "Statistics for Data Science", "lp": 10},
    {"name": "Machine Learning for Data Science", "lp": 10},
    {"name": "Programming for Data Science", "lp": 5},
]

LIFE_SCIENCES_MANDATORY = [
    {"name": "Data Science in Life Sciences", "lp": 15},
    {"name": "Forschungspraxis", "lp": 10},
    {"name": "Ethical Foundations of Data Science", "lp": 5},
]

TECHNOLOGIES_MANDATORY = [
    {"name": "Softwareprojekt Data Science A", "lp": 10},
    {"name": "Ethical Foundations of Data Science", "lp": 5},
]

THESIS = [{"name": "Masterarbeit mit begleitendem Kolloquium", "lp": 30, "area": "thesis"}]


def _codes(result, severity=None):
    return {
        issue.code
        for issue in result.issues
        if severity is None or issue.severity == severity
    }


def valid_life_sciences_plan() -> dict:
    return {
        "modules": [
            *GRUNDLAGEN,
            *LIFE_SCIENCES_MANDATORY,
            # 15 LP Life Sciences electives
            {"name": "Machine Learning in Bioinformatics", "lp": 5},
            {"name": "Big Data Analysis in Bioinformatics", "lp": 5},
            {"name": "Masterseminar Data Science in Life Sciences", "lp": 5},
            # 15 LP other-profile (Technologies) electives
            {"name": "Telematik", "lp": 10},
            {"name": "Mustererkennung", "lp": 5},
            *THESIS,
        ]
    }


def valid_technologies_plan() -> dict:
    return {
        "modules": [
            *GRUNDLAGEN,
            *TECHNOLOGIES_MANDATORY,
            # 30 LP Technologies electives
            {"name": "Höhere Algorithmik", "lp": 10},
            {"name": "Rechnersicherheit", "lp": 10},
            {"name": "Verteilte Systeme", "lp": 5},
            {"name": "Künstliche Intelligenz", "lp": 5},
            # 15 LP other-profile (Life Sciences) electives
            {"name": "Applied Machine Learning in Bioinformatics", "lp": 5},
            {"name": "Interdisziplinäre Zugänge im Rahmen von Data Science B", "lp": 10},
            *THESIS,
        ]
    }


def test_valid_life_sciences_plan_passes():
    result = validate_study_plan(valid_life_sciences_plan())

    assert result.is_valid, [issue.model_dump() for issue in result.issues]
    assert result.totals["grundlagen_lp"] == 30
    assert result.totals["own_profile_elective_lp"] == 15
    assert result.totals["other_profile_elective_lp"] == 15
    assert result.totals["module_area_lp"] == 90
    assert result.totals["thesis_lp"] == 30


def test_valid_technologies_plan_passes():
    result = validate_study_plan(valid_technologies_plan())

    assert result.is_valid, [issue.model_dump() for issue in result.issues]
    assert result.totals["own_profile_elective_lp"] == 30
    assert result.totals["other_profile_elective_lp"] == 15


def test_missing_grundlagen_module_is_reported():
    plan = valid_life_sciences_plan()
    plan["modules"] = [m for m in plan["modules"] if m["name"] != "Statistics for Data Science"]

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "grundlagen_incomplete" in _codes(result, "error")


def test_mixed_profiles_are_ambiguous():
    plan = valid_life_sciences_plan()
    plan["modules"].append({"name": "Softwareprojekt Data Science A", "lp": 10})

    result = validate_study_plan(plan)

    assert "profile_ambiguous" in _codes(result, "error")


def test_missing_profile_markers_is_unclear():
    result = validate_study_plan({"modules": [*GRUNDLAGEN, *THESIS]})

    assert "profile_unclear" in _codes(result, "error")


def test_elective_shortfall_is_reported():
    plan = valid_life_sciences_plan()
    plan["modules"] = [m for m in plan["modules"] if m["name"] != "Telematik"]

    result = validate_study_plan(plan)

    assert "other_profile_electives_lp" in _codes(result, "error")
    assert "module_area_lp_total" in _codes(result, "error")


def test_unknown_module_is_warning_not_silently_counted_toward_pools():
    plan = valid_life_sciences_plan()
    plan["modules"].append({"name": "Advanced Basket Weaving", "lp": 5})

    result = validate_study_plan(plan)

    assert "unmatched_modules" in _codes(result, "warning")
    # Unknown LP still counts toward the 90 LP total, which now overshoots.
    assert "module_area_lp_total" in _codes(result, "error")


def test_lp_mismatch_is_warning_and_duplicates_are_errors():
    plan = valid_life_sciences_plan()
    plan["modules"][0] = {"name": "Introduction to Profile Areas", "lp": 6}
    plan["modules"].append({"name": "Telematik", "lp": 10})

    result = validate_study_plan(plan)

    assert "module_lp_mismatch" in _codes(result, "warning")
    assert "duplicate_modules" in _codes(result, "error")


def test_missing_lp_falls_back_to_catalogue_value():
    plan = valid_life_sciences_plan()
    plan["modules"] = [
        {"name": m["name"], "lp": 0, **({"area": "thesis"} if m.get("area") == "thesis" else {})}
        if m["name"] == "Telematik"
        else m
        for m in plan["modules"]
    ]

    result = validate_study_plan(plan)

    assert result.is_valid, [issue.model_dump() for issue in result.issues]
    assert result.totals["other_profile_elective_lp"] == 15


def test_wrong_thesis_lp_is_reported():
    plan = valid_life_sciences_plan()
    plan["modules"][-1] = {"name": "Masterarbeit", "lp": 20, "area": "thesis"}

    result = validate_study_plan(plan)

    assert "master_thesis_lp" in _codes(result, "error")


def test_thesis_admission_warning_when_below_60_lp():
    result = validate_study_plan(
        {
            "modules": [
                *GRUNDLAGEN,
                {"name": "Data Science in Life Sciences", "lp": 15},
                *THESIS,
            ]
        }
    )

    assert "thesis_admission_lp" in _codes(result, "warning")
