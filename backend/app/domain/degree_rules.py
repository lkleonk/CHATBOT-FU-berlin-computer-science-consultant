from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.module_catalog import enrich_study_plan, normalize_module_name
from app.domain.study_plan import StudyPlan


class RuleIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RuleCheckResult(BaseModel):
    is_valid: bool
    summary: str
    totals: dict[str, int] = Field(default_factory=dict)
    issues: list[RuleIssue] = Field(default_factory=list)


INFORMATICS_AREAS = {"practical", "theoretical", "technical"}
SPECIALIZATION_MINIMUMS = {
    "practical": {"normal": 20, "specialization": 40},
    "technical": {"normal": 10, "specialization": 30},
    "theoretical": {"normal": 10, "specialization": 30},
}


def _sum_lp(plan: StudyPlan, predicate) -> int:
    return sum(module.lp for module in plan.modules if predicate(module))


def validate_study_plan(raw_plan: StudyPlan | dict[str, Any]) -> RuleCheckResult:
    plan = StudyPlan.model_validate(raw_plan)
    plan = enrich_study_plan(plan)
    issues: list[RuleIssue] = []

    def add_issue(code: str, severity: Literal["error", "warning"], message: str, **details: Any) -> None:
        issues.append(RuleIssue(code=code, severity=severity, message=message, details=details))

    for module in plan.modules:
        if module.lp <= 0:
            add_issue(
                "module_lp_missing",
                "error",
                f"Module '{module.name}' has no LP value.",
                module=module.name,
            )

    module_area_lp = _sum_lp(plan, lambda module: module.area != "thesis")
    thesis_lp = _sum_lp(plan, lambda module: module.area == "thesis")
    informatics_lp = _sum_lp(plan, lambda module: module.area in INFORMATICS_AREAS)
    application_lp = _sum_lp(plan, lambda module: module.area == "application")
    ungraded_lp = _sum_lp(plan, lambda module: module.is_ungraded)
    bachelor_lp = _sum_lp(plan, lambda module: module.is_bachelor_module)
    wahlbereich_lp = _sum_lp(plan, lambda module: module.is_wahlbereich)
    core_scientific_work_count = sum(
        1 for module in plan.modules if module.is_scientific_work and not module.is_wahlbereich
    )
    total_scientific_work_count = sum(1 for module in plan.modules if module.is_scientific_work)
    core_software_project_count = sum(
        1 for module in plan.modules if module.is_software_project and not module.is_wahlbereich
    )
    total_software_project_count = sum(1 for module in plan.modules if module.is_software_project)

    area_totals = {
        "practical_lp": _sum_lp(plan, lambda module: module.area == "practical"),
        "theoretical_lp": _sum_lp(plan, lambda module: module.area == "theoretical"),
        "technical_lp": _sum_lp(plan, lambda module: module.area == "technical"),
        "application_lp": application_lp,
        "informatics_lp": informatics_lp,
        "module_area_lp": module_area_lp,
        "thesis_lp": thesis_lp,
        "master_total_lp": module_area_lp + thesis_lp if thesis_lp else module_area_lp + 30,
        "ungraded_lp": ungraded_lp,
        "bachelor_module_lp": bachelor_lp,
        "wahlbereich_lp": wahlbereich_lp,
        "core_scientific_work_count": core_scientific_work_count,
        "total_scientific_work_count": total_scientific_work_count,
        "core_software_project_count": core_software_project_count,
        "total_software_project_count": total_software_project_count,
    }

    if module_area_lp != 90:
        add_issue(
            "module_area_lp_total",
            "error",
            "The module area before the thesis must total exactly 90 LP.",
            current_lp=module_area_lp,
            required_lp=90,
            delta=module_area_lp - 90,
        )

    if thesis_lp not in {0, 30}:
        add_issue(
            "master_thesis_lp",
            "error",
            "The Masterarbeit must count as 30 LP when it is included in the plan.",
            current_lp=thesis_lp,
            required_lp=30,
        )

    if not 70 <= informatics_lp <= 80:
        add_issue(
            "informatics_area_lp",
            "error",
            "The Informatik area must contain 70 to 80 LP.",
            current_lp=informatics_lp,
            minimum_lp=70,
            maximum_lp=80,
        )

    if not 10 <= application_lp <= 20:
        add_issue(
            "application_area_lp",
            "error",
            "The Anwendungsbereich must contain 10 to 20 LP.",
            current_lp=application_lp,
            minimum_lp=10,
            maximum_lp=20,
        )

    specialization = plan.specialization_area
    if specialization is None:
        add_issue(
            "specialization_missing",
            "error",
            "Exactly one specialization area must be selected: practical, theoretical, or technical.",
        )

    for area, limits in SPECIALIZATION_MINIMUMS.items():
        required_lp = limits["specialization"] if specialization == area else limits["normal"]
        current_lp = area_totals[f"{area}_lp"]
        if current_lp < required_lp:
            add_issue(
                f"{area}_minimum_lp",
                "error",
                f"{area.capitalize()} Informatics requires at least {required_lp} LP.",
                current_lp=current_lp,
                required_lp=required_lp,
                specialization_area=specialization,
            )

    if wahlbereich_lp > 10:
        add_issue(
            "wahlbereich_lp",
            "error",
            "The Wahlbereich can contain at most 10 LP.",
            current_lp=wahlbereich_lp,
            maximum_lp=10,
        )

    if core_scientific_work_count < 2 or core_scientific_work_count > 4:
        add_issue(
            "scientific_work_count",
            "error",
            "Students must complete at least 2 and at most 4 core Wissenschaftliches Arbeiten modules; extra Wissenschaftliches Arbeiten modules may be placed in the Wahlbereich.",
            current_count=core_scientific_work_count,
            minimum_count=2,
            maximum_count=4,
            total_count=total_scientific_work_count,
        )

    if specialization is not None:
        has_scientific_work_in_specialization = any(
            module.is_scientific_work and module.area == specialization and not module.is_wahlbereich
            for module in plan.modules
        )
        if not has_scientific_work_in_specialization:
            add_issue(
                "scientific_work_specialization",
                "error",
                "At least one Wissenschaftliches Arbeiten module must be from the specialization area.",
                specialization_area=specialization,
            )

    if core_software_project_count < 1 or core_software_project_count > 2:
        add_issue(
            "software_project_count",
            "error",
            "Students must complete at least 1 and at most 2 core Softwareprojekt modules; one extra Softwareprojekt may be placed in the Wahlbereich.",
            current_count=core_software_project_count,
            minimum_count=1,
            maximum_count=2,
            total_count=total_software_project_count,
        )

    if not 25 <= ungraded_lp <= 30:
        add_issue(
            "ungraded_lp",
            "error",
            "Ungraded or non-differentiated modules must total 25 to 30 LP.",
            current_lp=ungraded_lp,
            minimum_lp=25,
            maximum_lp=30,
        )

    if bachelor_lp > 15:
        add_issue(
            "bachelor_module_lp",
            "error",
            "Bachelor modules can only be counted up to 15 LP.",
            current_lp=bachelor_lp,
            maximum_lp=15,
        )

    normalized_names = [normalize_module_name(module.name) for module in plan.modules if module.name.strip()]
    duplicate_names = sorted(name for name, count in Counter(normalized_names).items() if count > 1)
    if duplicate_names:
        add_issue(
            "duplicate_modules",
            "error",
            "The same exact module cannot count twice.",
            duplicate_normalized_names=duplicate_names,
        )

    unknown_area_modules = [
        module.name for module in plan.modules if module.area == "unknown" and module.area != "thesis"
    ]
    if unknown_area_modules:
        add_issue(
            "unknown_module_area",
            "warning",
            "Some modules could not be assigned to an area; verify their official area manually.",
            modules=unknown_area_modules,
        )

    is_valid = not any(issue.severity == "error" for issue in issues)
    if is_valid:
        summary = "The supplied study plan satisfies the implemented 2014 Master Informatik checks."
    else:
        error_count = sum(1 for issue in issues if issue.severity == "error")
        summary = f"The supplied study plan has {error_count} blocking issue(s) under the implemented checks."

    return RuleCheckResult(
        is_valid=is_valid,
        summary=summary,
        totals=area_totals,
        issues=issues,
    )
