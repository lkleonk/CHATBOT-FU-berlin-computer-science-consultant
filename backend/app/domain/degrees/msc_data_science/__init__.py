from app.domain.degrees.definition import DegreeDefinition, DegreePrompts
from app.domain.degrees.msc_data_science import prompts
from app.domain.degrees.msc_data_science.degree_rules import validate_study_plan
from app.domain.degrees.msc_data_science.module_catalog import ALL_MODULES, enrich_study_plan
from app.domain.degrees.msc_data_science.program_rules import get_program_rules


DEGREE = DegreeDefinition(
    id="msc_data_science",
    display_name="M.Sc. Data Science",
    regulation="2021 Studien- und Pruefungsordnung (FU-Mitteilungen 18/2021)",
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
    course_areas=("grundlagen", "life_sciences", "technologies"),
    course_modules={module.id: module.name for module in ALL_MODULES},
)
