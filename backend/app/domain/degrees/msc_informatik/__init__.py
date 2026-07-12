from app.domain.degrees.definition import DegreeDefinition, DegreePrompts
from app.domain.degrees.msc_informatik import prompts
from app.domain.degrees.msc_informatik.degree_rules import validate_study_plan
from app.domain.degrees.msc_informatik.program_rules import get_program_rules
from app.domain.module_catalog import enrich_study_plan


DEGREE = DegreeDefinition(
    id="msc_informatik",
    display_name="M.Sc. Informatik",
    regulation="2014 Studien- und Pruefungsordnung",
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
    course_areas=("technical", "practical", "theoretical", "application"),
    course_modules=None,
)
