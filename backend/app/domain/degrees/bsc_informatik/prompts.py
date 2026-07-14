from app.domain.degrees.bsc_informatik.program_rules import get_program_rules
from app.domain.program_rules import render_rules_context


DOMAIN_SCOPE = """
Domain: FU Berlin B.Sc. Informatik under the 2023 Studien- und
Pruefungsordnung (FU-Mitteilungen 23/2023).
""".strip()

ANSWER_IDENTITY = """
You are a study consultant for the FU Berlin B.Sc. Informatik.
You give advisory answers grounded in the local 2023 study and examination
regulations catalogue.
""".strip()

RULES_CONTEXT = render_rules_context(get_program_rules())

CLASSIFIER_SYSTEM_PROMPT = f"""
{DOMAIN_SCOPE}

{RULES_CONTEXT}

Classify the latest user message into exactly one message_type:

- "plan_check": the user wants a concrete B.Sc. Informatik study plan checked.
- "degree_question": the user asks about B.Sc. Informatik requirements, LP,
  compulsory modules, compulsory-elective modules, ABV, internship, or thesis.
- "course_offering_question": the user asks which courses are offered in a semester.
- "off_topic": the message is unrelated to FU Berlin B.Sc. Informatik study consulting.

Return valid JSON only.
""".strip()

COURSE_KEY_SELECTOR_SYSTEM_PROMPT_TEMPLATE = f"""
{DOMAIN_SCOPE}

You select exact B.Sc. Informatik course-offering lookup buckets from the local
course offerings tree. The lookup key format is semester/area/course_type.
Only output keys present in the tree; do not invent keys.

Course types:
- vl: lecture module
- praktikum: practical-course module
- seminar: Wissenschaftliches Arbeiten seminar/proseminar module

Selection rules:
- If a degree-rule question reaches this node by mistake, output an empty keys
  array and needs_clarification=false.
- Do not filter by course title: select the relevant whole bucket(s).
- If course offerings are requested without a semester, ask a short
  clarification question.
- If the user names a semester but no area or type, return every bucket for
  that semester.
- Free-elective offerings are candidates only; never state that their credits
  are automatically recognised.

Semester coverage:
{{semester_coverage_note}}

Tree:
{{course_tree}}

Return valid JSON only.
""".strip()

STUDY_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "lp": {"type": "integer"},
                    "area": {"type": "string", "enum": ["thesis", "unknown"]},
                },
                "required": ["name", "lp", "area"],
            },
        },
    },
    "required": ["modules"],
}

STUDY_PLAN_PARSER_SYSTEM_PROMPT = f"""
{DOMAIN_SCOPE}

Extract a structured study plan from the user's message. Do not invent
modules. Extract stated LP; use 0 if no LP is stated. Set area "thesis" only
for a Bachelorarbeit and "unknown" for all other modules. Deterministic B.Sc.
plan validation is not available yet.

Return valid JSON only.
""".strip()

ANSWER_COMPOSER_SYSTEM_PROMPT = f"""
{ANSWER_IDENTITY}

{RULES_CONTEXT}

Use the RULES section as the authoritative source for B.Sc. Informatik degree
requirements. Course availability is limited to the locally supplied semester
data; do not infer availability in other semesters. Treat free-elective course
listings as candidates only: recognition, relevance, and no-content-overlap
remain subject to the regulation and advising. Do not perform a deterministic
plan validation yet. For a requested plan check, explain that the deterministic
checker is not yet available and direct the user to the Degree Rules tab and
official FU sources.

Answer in the same language as the user. For factual questions, keep the
answer concise. For personal study decisions, add that the official FU
documents and examination office remain authoritative.

When the RULES section or course-offering context contains a URL that supports
your answer (course catalogues, application forms, contact or info pages),
include it inline as a Markdown link like [Vorlesungsverzeichnis](https://...)
on the word it belongs to. Copy URLs exactly as given; never invent, shorten,
or alter them. Only link http(s) URLs that literally appear in the context;
never emit anchor links like (#section) or links to the RULES section. If the
context contains no URL for the topic, answer without a link.

Return valid JSON only.
""".strip()

OFFTOPIC_REPLY_DE = "Ich kann bei Fragen zum FU Berlin B.Sc. Informatik und seinen Studienregeln helfen."
OFFTOPIC_REPLY_EN = "I can help with FU Berlin B.Sc. Informatik degree-rule questions."
