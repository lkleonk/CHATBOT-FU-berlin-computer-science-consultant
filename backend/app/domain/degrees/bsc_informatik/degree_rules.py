"""Temporary study-plan response for B.Sc. Informatik.

The regulation catalogue is available, but deterministic plan checking needs
the canonical module and ABV mappings that are not part of the repository yet.
"""

from typing import Any

from app.domain.rule_check import RuleCheckResult, RuleIssue
from app.domain.study_plan import StudyPlan


def validate_study_plan(raw_plan: StudyPlan | dict[str, Any]) -> RuleCheckResult:
    plan = StudyPlan.model_validate(raw_plan)
    return RuleCheckResult(
        is_valid=False,
        summary=(
            "B.Sc. Informatik 2023 plan checking is not available yet because the canonical "
            "module and ABV catalogue has not been added. The Degree Rules tab lists the "
            "current requirements."
        ),
        totals={"listed_module_lp": sum(module.lp for module in plan.modules)},
        issues=[
            RuleIssue(
                code="bsc_plan_validation_unavailable",
                severity="warning",
                message=(
                    "No deterministic B.Sc. Informatik plan validation is available until the "
                    "canonical module and ABV catalogue is added."
                ),
            )
        ],
    )
