"""FU Berlin B.Sc. Informatik, 2023 study and examination regulations.

This initial degree package intentionally provides the authoritative rules
catalogue only. Canonical module mappings, course offerings, and deterministic
study-plan validation will be added once their source data is available.
"""

from app.domain.degrees.definition import DegreeDefinition, DegreePrompts
from app.domain.degrees.bsc_informatik import prompts
from app.domain.degrees.bsc_informatik.degree_rules import validate_study_plan
from app.domain.degrees.bsc_informatik.program_rules import get_program_rules
from app.domain.catalog_data import module_names
from app.domain.study_plan import StudyPlan


def enrich_study_plan(plan: StudyPlan) -> StudyPlan:
    """Leave B.Sc. plans unchanged until a canonical module catalogue exists."""
    return plan


DEGREE = DegreeDefinition(
    id="bsc_informatik",
    display_name="B.Sc. Informatik",
    regulation="2023 Studien- und Pruefungsordnung (FU-Mitteilungen 23/2023)",
    prompts=DegreePrompts(
        domain_scope=prompts.DOMAIN_SCOPE,
        answer_identity=prompts.ANSWER_IDENTITY,
        classifier_system_prompt=prompts.CLASSIFIER_SYSTEM_PROMPT,
        course_key_selector_template=prompts.COURSE_KEY_SELECTOR_SYSTEM_PROMPT_TEMPLATE,
        study_plan_parser_system_prompt=prompts.STUDY_PLAN_PARSER_SYSTEM_PROMPT,
        answer_composer_system_prompt=prompts.ANSWER_COMPOSER_SYSTEM_PROMPT,
        offtopic_reply_de=prompts.OFFTOPIC_REPLY_DE,
        offtopic_reply_en=prompts.OFFTOPIC_REPLY_EN,
    ),
    get_program_rules=get_program_rules,
    validate_study_plan=validate_study_plan,
    study_plan_schema=prompts.STUDY_PLAN_SCHEMA,
    enrich_study_plan=enrich_study_plan,
    course_areas=("compulsory", "compulsory_elective", "free_elective", "abv"),
    course_modules=module_names("bsc_informatik"),
)
