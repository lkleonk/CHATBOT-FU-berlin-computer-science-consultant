from functools import lru_cache

from pydantic import BaseModel, Field


class ProgramRuleSource(BaseModel):
    label: str
    path: str
    note: str | None = None


class ProgramRuleItem(BaseModel):
    label: str
    text: str
    minimum: int | None = None
    maximum: int | None = None
    unit: str | None = None


class ProgramRuleSection(BaseModel):
    id: str
    title: str
    description: str
    items: list[ProgramRuleItem] = Field(default_factory=list)
    related_issue_codes: list[str] = Field(default_factory=list)
    sources: list[ProgramRuleSource] = Field(default_factory=list)


class ProgramRulesCatalogue(BaseModel):
    degree_program: str
    regulation: str
    catalogue_version: str
    source_note: str
    sections: list[ProgramRuleSection]


DEFAULT_SOURCES = [
    ProgramRuleSource(
        label="Informatik Master Ablauf",
        path="ressources/Informatik_Master_Ablauf.txt",
    ),
    ProgramRuleSource(
        label="Checkliste Master Informatik 2014",
        path="ressources/Checkliste-MSc-Informatik-_2014_.pdf",
    ),
]


@lru_cache(maxsize=1)
def get_program_rules() -> ProgramRulesCatalogue:
    return ProgramRulesCatalogue(
        degree_program="FU Berlin Master Informatik",
        regulation="2014 study and examination checklist",
        catalogue_version="master-informatik-2014-v1",
        source_note=(
            "Overview of the official degree requirements for the FU Berlin Master Informatik "
            "(2014 study regulations). Use this catalogue as a reference; for a binding plan check, "
            "submit your study plan in the Chat tab."
        ),
        sections=[
            ProgramRuleSection(
                id="overall-structure",
                title="Overall Structure",
                description=(
                    "The Master Informatik comprises 120 LP in total: 90 LP of modules before the thesis "
                    "and a 30 LP Masterarbeit. The regular study duration is 4 semesters."
                ),
                items=[
                    ProgramRuleItem(label="Total degree volume", text="120 LP total", minimum=120, maximum=120, unit="LP"),
                    ProgramRuleItem(
                        label="Module area before thesis",
                        text="Exactly 90 LP must be completed before the Masterarbeit.",
                        minimum=90,
                        maximum=90,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Masterarbeit",
                        text="The Masterarbeit counts as 30 LP when included in the plan.",
                        minimum=30,
                        maximum=30,
                        unit="LP",
                    ),
                    ProgramRuleItem(label="Compulsory modules", text="There are no compulsory modules."),
                ],
                related_issue_codes=["module_area_lp_total", "master_thesis_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="informatics-area",
                title="Informatik Area",
                description=(
                    "The Informatik area contains the practical, technical, and theoretical study areas. "
                    "Exactly one of these areas must be selected as the specialization area."
                ),
                items=[
                    ProgramRuleItem(
                        label="Informatik total",
                        text="The Informatik area must contain 70 to 80 LP.",
                        minimum=70,
                        maximum=80,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Praktische Informatik",
                        text="At least 20 LP, or at least 40 LP if it is the specialization area.",
                        minimum=20,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Technische Informatik",
                        text="At least 10 LP, or at least 30 LP if it is the specialization area.",
                        minimum=10,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Theoretische Informatik",
                        text="At least 10 LP, or at least 30 LP if it is the specialization area.",
                        minimum=10,
                        unit="LP",
                    ),
                ],
                related_issue_codes=[
                    "informatics_area_lp",
                    "specialization_missing",
                    "practical_minimum_lp",
                    "technical_minimum_lp",
                    "theoretical_minimum_lp",
                ],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="application-area",
                title="Anwendungsbereich",
                description=(
                    "The Anwendungsbereich, formerly Nebenfach, is counted separately from the Informatik area."
                ),
                items=[
                    ProgramRuleItem(
                        label="Application area LP",
                        text="The Anwendungsbereich must contain 10 to 20 LP.",
                        minimum=10,
                        maximum=20,
                        unit="LP",
                    ),
                ],
                related_issue_codes=["application_area_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="wissenschaftliches-arbeiten",
                title="Wissenschaftliches Arbeiten",
                description=(
                    "Students must complete Wissenschaftliches Arbeiten modules in the core Informatik selection. "
                    "Additional modules can be placed in Wahlbereich under the 10 LP Wahlbereich cap."
                ),
                items=[
                    ProgramRuleItem(
                        label="Core count",
                        text="At least 2 and at most 4 core Wissenschaftliches Arbeiten modules are required.",
                        minimum=2,
                        maximum=4,
                        unit="modules",
                    ),
                    ProgramRuleItem(
                        label="Specialization coverage",
                        text="At least one Wissenschaftliches Arbeiten module must be from the specialization area.",
                        minimum=1,
                        unit="module",
                    ),
                    ProgramRuleItem(
                        label="Wahlbereich caveat",
                        text=(
                            "Up to 2 additional Wissenschaftliches Arbeiten modules can be placed in Wahlbereich, "
                            "because each seminar has 5 LP and Wahlbereich has 10 LP."
                        ),
                        maximum=2,
                        unit="additional modules",
                    ),
                    ProgramRuleItem(
                        label="Duplicate modules",
                        text="The same exact Wissenschaftliches Arbeiten module can only be counted once.",
                    ),
                ],
                related_issue_codes=[
                    "scientific_work_count",
                    "scientific_work_specialization",
                    "duplicate_modules",
                    "wahlbereich_lp",
                ],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="softwareprojekt",
                title="Softwareprojekt",
                description=(
                    "Students must complete Softwareprojekt modules in the core Informatik selection. "
                    "A third Softwareprojekt is possible only when one Softwareprojekt is counted in Wahlbereich."
                ),
                items=[
                    ProgramRuleItem(
                        label="Core count",
                        text="At least 1 and at most 2 core Softwareprojekt modules are required.",
                        minimum=1,
                        maximum=2,
                        unit="modules",
                    ),
                    ProgramRuleItem(
                        label="Wahlbereich caveat",
                        text=(
                            "One additional Softwareprojekt can be placed in Wahlbereich, allowing 3 "
                            "Softwareprojekt modules total when the Wahlbereich cap is still respected."
                        ),
                        maximum=1,
                        unit="additional module",
                    ),
                    ProgramRuleItem(
                        label="Grading",
                        text="Softwareprojekt A is graded; Softwareprojekt B is ungraded.",
                    ),
                ],
                related_issue_codes=["software_project_count", "wahlbereich_lp", "ungraded_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="wahlbereich",
                title="Wahlbereich",
                description=(
                    "Wahlbereich is tracked separately from the module's academic area. This matters for the "
                    "seminar and Softwareprojekt caveats."
                ),
                items=[
                    ProgramRuleItem(
                        label="LP cap",
                        text="The Wahlbereich can contain at most 10 LP.",
                        maximum=10,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Area identity",
                        text=(
                            "A module can still belong to practical, technical, theoretical, or application area "
                            "while being counted in Wahlbereich for caveat handling."
                        ),
                    ),
                ],
                related_issue_codes=["wahlbereich_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="ungraded-modules",
                title="Ungraded Modules",
                description=(
                    "Modules with non-differentiated assessment or no assessment are capped across the full plan."
                ),
                items=[
                    ProgramRuleItem(
                        label="Ungraded LP",
                        text="Ungraded or non-differentiated modules must total 25 to 30 LP.",
                        minimum=25,
                        maximum=30,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Known examples",
                        text=(
                            "Known ungraded modules include Wissenschaftliches Arbeiten, Softwareprojekt B, "
                            "Projektmanagement, Projektmanagement - Vertiefung, Grundlagen des Managements "
                            "von IT-Projekten, Praktiken professioneller Softwareentwicklung, and "
                            "Existenzgruendung in der IT-Industrie."
                        ),
                    ),
                ],
                related_issue_codes=["ungraded_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="bachelor-modules",
                title="Bachelor Modules",
                description="Bachelor modules can be included only within a strict LP cap.",
                items=[
                    ProgramRuleItem(
                        label="Bachelor-module LP",
                        text="Bachelor modules can only be counted up to 15 LP.",
                        maximum=15,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Application modules",
                        text=(
                            "Application-area modules may also be Bachelor modules and must be included in this "
                            "15 LP cap when applicable."
                        ),
                    ),
                ],
                related_issue_codes=["bachelor_module_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="duplicates",
                title="Duplicate Modules",
                description="The same exact module cannot count twice in the Master.",
                items=[
                    ProgramRuleItem(
                        label="Exact duplicate",
                        text="The same exact module cannot count twice in the Master.",
                    ),
                    ProgramRuleItem(
                        label="Previously used Master modules",
                        text=(
                            "A Master module already used in a prior Bachelor specialization cannot be reused "
                            "for the Master."
                        ),
                    ),
                ],
                related_issue_codes=["duplicate_modules"],
                sources=DEFAULT_SOURCES,
            ),
        ],
    )


@lru_cache(maxsize=1)
def render_program_rules_context() -> str:
    """Render the structured rule catalogue for LLM prompts.

    The structured catalogue remains the source of human-readable rule text.
    This renderer provides a compact prompt projection so the Degree Rules tab
    and user-facing answer composer do not drift apart.
    """

    catalogue = get_program_rules()
    lines = [
        f"{catalogue.degree_program} - {catalogue.regulation}",
        "",
        catalogue.source_note,
    ]

    for section in catalogue.sections:
        lines.extend(["", section.title.upper(), f"- {section.description}"])
        for item in section.items:
            lines.append(f"- {item.label}: {item.text}")

    return "\n".join(lines).strip()
