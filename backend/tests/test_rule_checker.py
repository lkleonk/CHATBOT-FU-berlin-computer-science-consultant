from app.domain.degrees.msc_informatik.degree_rules import validate_study_plan


def issue_codes(result):
    return {issue.code for issue in result.issues}


def valid_plan():
    return {
        "specialization_area": "practical",
        "modules": [
            {"name": "Softwareprojekt Praktische Informatik B"},
            {"name": "Wissenschaftliches Arbeiten Praktische Informatik A"},
            {"name": "Projektmanagement"},
            {"name": "Künstliche Intelligenz"},
            {"name": "Datenbanktechnologie"},
            {"name": "Rechnersicherheit"},
            {"name": "Algorithmische Geometrie"},
            {"name": "Modelchecking"},
            {"name": "Betriebssysteme"},
            {"name": "Wissenschaftliches Arbeiten Technische Informatik A"},
            {"name": "Mobilkommunikation"},
            {"name": "Anwendungsmodul A", "lp": 10, "area": "application"},
            {"name": "Masterarbeit"},
        ],
    }


def test_valid_plan_passes():
    result = validate_study_plan(valid_plan())

    assert result.is_valid
    assert result.totals["module_area_lp"] == 90
    assert result.totals["informatics_lp"] == 80
    assert result.totals["application_lp"] == 10
    assert result.totals["ungraded_lp"] == 25
    assert result.totals["core_software_project_count"] == 1
    assert result.totals["core_scientific_work_count"] == 2


def test_missing_specialization_lp_fails():
    plan = valid_plan()
    plan["specialization_area"] = "technical"

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "technical_minimum_lp" in issue_codes(result)


def test_too_many_ungraded_lp_fails():
    plan = valid_plan()
    plan["modules"][-2]["is_ungraded"] = True

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "ungraded_lp" in issue_codes(result)


def test_too_many_bachelor_module_lp_fails():
    plan = valid_plan()
    plan["modules"][-2]["lp"] = 20
    plan["modules"][-2]["is_bachelor_module"] = True

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "bachelor_module_lp" in issue_codes(result)


def test_too_few_scientific_work_modules_fails():
    plan = valid_plan()
    plan["modules"] = [
        module
        for module in plan["modules"]
        if module["name"] != "Wissenschaftliches Arbeiten Technische Informatik A"
    ]
    plan["modules"].append({"name": "Telematik"})

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "scientific_work_count" in issue_codes(result)


def test_too_many_software_projects_fails():
    plan = valid_plan()
    plan["modules"].append({"name": "Softwareprojekt - Technische Informatik A"})
    plan["modules"].append({"name": "Softwareprojekt - Theoretische Informatik A"})

    result = validate_study_plan(plan)

    assert not result.is_valid
    assert "software_project_count" in issue_codes(result)


def test_third_software_project_allowed_when_in_wahlbereich():
    plan = valid_plan()
    plan["modules"] = [
        {"name": "Softwareprojekt Praktische Informatik B"},
        {"name": "Softwareprojekt - Theoretische Informatik A"},
        {
            "name": "Softwareprojekt - Technische Informatik A",
            "is_wahlbereich": True,
        },
        {"name": "Wissenschaftliches Arbeiten Praktische Informatik A"},
        {"name": "Projektmanagement"},
        {"name": "Künstliche Intelligenz"},
        {"name": "Datenbanktechnologie"},
        {"name": "Rechnersicherheit"},
        {"name": "Algorithmische Geometrie"},
        {"name": "Wissenschaftliches Arbeiten Technische Informatik A"},
        {"name": "Mobilkommunikation"},
        {"name": "Anwendungsmodul A", "lp": 10, "area": "application"},
        {"name": "Masterarbeit"},
    ]

    result = validate_study_plan(plan)

    assert result.is_valid
    assert result.totals["core_software_project_count"] == 2
    assert result.totals["total_software_project_count"] == 3
    assert result.totals["wahlbereich_lp"] == 10


def test_two_extra_scientific_work_modules_allowed_when_in_wahlbereich():
    plan = {
        "specialization_area": "practical",
        "modules": [
            {"name": "Softwareprojekt Praktische Informatik A"},
            {"name": "Wissenschaftliches Arbeiten Praktische Informatik A"},
            {"name": "Wissenschaftliches Arbeiten Praktische Informatik B"},
            {"name": "Wissenschaftliches Arbeiten Technische Informatik A"},
            {"name": "Wissenschaftliches Arbeiten Technische Informatik B"},
            {
                "name": "Wissenschaftliches Arbeiten Theoretische Informatik A",
                "is_wahlbereich": True,
            },
            {
                "name": "Wissenschaftliches Arbeiten Theoretische Informatik B",
                "is_wahlbereich": True,
            },
            {"name": "Künstliche Intelligenz"},
            {"name": "Datenbanktechnologie"},
            {"name": "Rechnersicherheit"},
            {"name": "Telematik"},
            {"name": "Algorithmische Geometrie"},
            {"name": "Anwendungsmodul A", "lp": 10, "area": "application"},
            {"name": "Masterarbeit"},
        ],
    }

    result = validate_study_plan(plan)

    assert result.is_valid
    assert result.totals["core_scientific_work_count"] == 4
    assert result.totals["total_scientific_work_count"] == 6
    assert result.totals["wahlbereich_lp"] == 10
