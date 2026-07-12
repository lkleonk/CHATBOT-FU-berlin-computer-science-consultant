"""Deterministic study-plan validation for the M.Sc. Data Science.

Checklist-style validation: parsed module names are matched against the
canonical catalogue in ``module_catalog.py``; the chosen profile is inferred
from the profile-specific mandatory modules that are present, per the 2021
order ("the chosen profile is determined by taking the corresponding
mandatory modules").
"""

from collections import Counter
from typing import Any, Literal

from app.domain.degrees.msc_data_science.module_catalog import (
    GRUNDLAGEN_IDS,
    PROFILES,
    THESIS_MODULE,
    CatalogModule,
    Profile,
    find_module,
    modules_by_id,
)
from app.domain.module_catalog import normalize_module_name
from app.domain.rule_check import RuleCheckResult, RuleIssue
from app.domain.study_plan import PlannedModule, StudyPlan


def _effective_lp(module: PlannedModule, record: CatalogModule | None) -> int:
    if module.lp > 0:
        return module.lp
    if record is not None and record.lp is not None:
        return record.lp
    return 0


def _is_thesis(module: PlannedModule, record: CatalogModule | None) -> bool:
    if record is not None and record.id == THESIS_MODULE.id:
        return True
    return module.area == "thesis" or "masterarbeit" in normalize_module_name(module.name)


def validate_study_plan(raw_plan: StudyPlan | dict[str, Any]) -> RuleCheckResult:
    plan = StudyPlan.model_validate(raw_plan)
    issues: list[RuleIssue] = []

    def add_issue(code: str, severity: Literal["error", "warning"], message: str, **details: Any) -> None:
        issues.append(RuleIssue(code=code, severity=severity, message=message, details=details))

    matched: list[tuple[PlannedModule, CatalogModule]] = []
    unmatched: list[PlannedModule] = []
    thesis_lp = 0

    for module in plan.modules:
        record = find_module(module.name)
        if _is_thesis(module, record):
            thesis_lp += _effective_lp(module, THESIS_MODULE)
            continue
        if record is not None:
            matched.append((module, record))
            if module.lp > 0 and record.lp is not None and module.lp != record.lp:
                add_issue(
                    "module_lp_mismatch",
                    "warning",
                    f"Module '{record.name}' is stated with {module.lp} LP but the catalogue lists {record.lp} LP.",
                    module=record.name,
                    stated_lp=module.lp,
                    catalogue_lp=record.lp,
                )
        else:
            unmatched.append(module)
        if _effective_lp(module, record) <= 0:
            add_issue(
                "module_lp_missing",
                "error",
                f"Module '{module.name}' has no LP value.",
                module=module.name,
            )

    matched_ids = {record.id for _, record in matched}

    def lp_of(ids: set[str] | tuple[str, ...]) -> int:
        wanted = set(ids)
        return sum(
            _effective_lp(module, record) for module, record in matched if record.id in wanted
        )

    grundlagen_lp = lp_of(GRUNDLAGEN_IDS)
    unmatched_lp = sum(_effective_lp(module, None) for module in unmatched)

    missing_grundlagen = [
        modules_by_id()[module_id].name for module_id in GRUNDLAGEN_IDS if module_id not in matched_ids
    ]
    if missing_grundlagen:
        add_issue(
            "grundlagen_incomplete",
            "error",
            "All four Grundlagenbereich modules (30 LP) are mandatory.",
            missing_modules=missing_grundlagen,
        )

    profile = _infer_profile(matched_ids, add_issue)

    profile_mandatory_lp = 0
    own_elective_lp = 0
    other_elective_lp = 0
    if profile is not None:
        mandatory_ids = set(profile.mandatory_ids)
        profile_mandatory_lp = lp_of(mandatory_ids)
        own_elective_lp = lp_of(set(profile.own_elective_ids) - mandatory_ids)
        other_elective_lp = lp_of(set(profile.other_elective_ids) - mandatory_ids)

        missing_mandatory = [
            modules_by_id()[module_id].name
            for module_id in profile.mandatory_ids
            if module_id not in matched_ids
        ]
        if missing_mandatory:
            add_issue(
                "profile_mandatory_missing",
                "error",
                f"The profile '{profile.display_name}' requires its mandatory modules.",
                profile=profile.id,
                missing_modules=missing_mandatory,
            )

        _check_elective_lp(
            add_issue,
            code="own_profile_electives_lp",
            label=f"electives from the {profile.display_name} profile list",
            current_lp=own_elective_lp,
            required_lp=profile.own_elective_lp,
            profile=profile.id,
        )
        _check_elective_lp(
            add_issue,
            code="other_profile_electives_lp",
            label="electives from the other-profile list",
            current_lp=other_elective_lp,
            required_lp=profile.other_elective_lp,
            profile=profile.id,
        )

    if unmatched:
        add_issue(
            "unmatched_modules",
            "warning",
            "Some modules are not in the local Data Science module catalogue and cannot be "
            "counted deterministically. Up to 15 LP from other Master's programs may replace "
            "other-profile electives only with Prüfungsausschuss approval.",
            modules=[module.name for module in unmatched],
        )

    module_area_lp = grundlagen_lp + profile_mandatory_lp + own_elective_lp + other_elective_lp + unmatched_lp
    if module_area_lp != 90:
        add_issue(
            "module_area_lp_total",
            "error",
            "The module area before the thesis must total exactly 90 LP "
            "(30 LP Grundlagenbereich + 60 LP Profilbereich).",
            current_lp=module_area_lp,
            required_lp=90,
            delta=module_area_lp - 90,
        )

    if thesis_lp not in {0, 30}:
        add_issue(
            "master_thesis_lp",
            "error",
            "The Masterarbeit with accompanying colloquium must count as 30 LP when it is included in the plan.",
            current_lp=thesis_lp,
            required_lp=30,
        )

    if thesis_lp > 0 and module_area_lp < 60:
        add_issue(
            "thesis_admission_lp",
            "warning",
            "Admission to the Masterarbeit requires at least 60 LP completed in the program.",
            current_lp=module_area_lp,
            minimum_lp=60,
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

    totals = {
        "grundlagen_lp": grundlagen_lp,
        "profile_mandatory_lp": profile_mandatory_lp,
        "own_profile_elective_lp": own_elective_lp,
        "other_profile_elective_lp": other_elective_lp,
        "unmatched_lp": unmatched_lp,
        "module_area_lp": module_area_lp,
        "thesis_lp": thesis_lp,
        "master_total_lp": module_area_lp + thesis_lp if thesis_lp else module_area_lp + 30,
    }

    is_valid = not any(issue.severity == "error" for issue in issues)
    if is_valid:
        summary = "The supplied study plan satisfies the implemented 2021 M.Sc. Data Science checks."
    else:
        error_count = sum(1 for issue in issues if issue.severity == "error")
        summary = f"The supplied study plan has {error_count} blocking issue(s) under the implemented checks."

    return RuleCheckResult(is_valid=is_valid, summary=summary, totals=totals, issues=issues)


def _infer_profile(matched_ids: set[str], add_issue) -> Profile | None:
    detected = [
        profile
        for profile in PROFILES.values()
        if any(marker in matched_ids for marker in profile.marker_ids)
    ]
    if len(detected) == 1:
        return detected[0]

    if len(detected) > 1:
        add_issue(
            "profile_ambiguous",
            "error",
            "Mandatory modules from both profiles are present, but exactly one profile "
            "(Data Science in Life Sciences or Data Science Technologies) must be completed.",
            detected_profiles=[profile.id for profile in detected],
        )
    else:
        add_issue(
            "profile_unclear",
            "error",
            "No profile could be determined. The chosen profile is determined by taking its "
            "mandatory modules (Life Sciences: Data Science in Life Sciences, Forschungspraxis; "
            "Technologies: Softwareprojekt Data Science A).",
        )
    return None


def _check_elective_lp(add_issue, code: str, label: str, current_lp: int, required_lp: int, profile: str) -> None:
    if current_lp < required_lp:
        add_issue(
            code,
            "error",
            f"Exactly {required_lp} LP of {label} are required.",
            current_lp=current_lp,
            required_lp=required_lp,
            profile=profile,
        )
    elif current_lp > required_lp:
        add_issue(
            code,
            "warning",
            f"More than the required {required_lp} LP of {label} are planned; "
            "the excess does not count toward the degree.",
            current_lp=current_lp,
            required_lp=required_lp,
            profile=profile,
        )
