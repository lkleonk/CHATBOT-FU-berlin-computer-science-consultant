from functools import lru_cache

from app.domain.degrees.msc_data_science.module_catalog import (
    GRUNDLAGEN_MODULES,
    INTERDISCIPLINARY_MODULES,
    LIFE_SCIENCES_ELECTIVE_MODULES,
    LIFE_SCIENCES_MANDATORY_MODULES,
    TECHNOLOGIES_ELECTIVE_MODULES,
    CatalogModule,
)
from app.domain.program_rules import (
    ProgramRuleItem,
    ProgramRuleSection,
    ProgramRuleSource,
    ProgramRulesCatalogue,
)


DEFAULT_SOURCES = [
    ProgramRuleSource(
        label="Studien- und Pruefungsordnung M.Sc. Data Science (FU-Mitteilungen 18/2021)",
        path="docs/data_science_master.md",
    ),
]


def _module_item(module: CatalogModule) -> ProgramRuleItem:
    lp_text = f"{module.lp} LP" if module.lp is not None else "LP varies (see module catalogue)"
    return ProgramRuleItem(
        label=module.name,
        text=f"{module.name} ({lp_text})",
        minimum=module.lp,
        maximum=module.lp,
        unit="LP" if module.lp is not None else None,
    )


@lru_cache(maxsize=1)
def get_program_rules() -> ProgramRulesCatalogue:
    return ProgramRulesCatalogue(
        degree_program="FU Berlin M.Sc. Data Science",
        regulation="2021 study and examination regulations (FU-Mitteilungen 18/2021)",
        catalogue_version="msc-data-science-2021-v1",
        source_note=(
            "Overview of the official degree requirements for the FU Berlin M.Sc. Data Science "
            "(2021 study regulations, joint program of Fachbereich Mathematik und Informatik and "
            "Fachbereich Erziehungswissenschaft und Psychologie). Use this catalogue as a reference; "
            "for a binding plan check, submit your study plan in the Chat tab."
        ),
        sections=[
            ProgramRuleSection(
                id="overall-structure",
                title="Overall Structure",
                description=(
                    "The M.Sc. Data Science comprises 120 LP in total: 30 LP Grundlagenbereich, "
                    "60 LP Profilbereich, and a 30 LP Masterarbeit with accompanying colloquium. "
                    "The regular study duration is 4 semesters."
                ),
                items=[
                    ProgramRuleItem(label="Total degree volume", text="120 LP total", minimum=120, maximum=120, unit="LP"),
                    ProgramRuleItem(
                        label="Grundlagenbereich",
                        text="30 LP of mandatory foundation modules.",
                        minimum=30,
                        maximum=30,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Profilbereich",
                        text="60 LP in exactly one of two profiles.",
                        minimum=60,
                        maximum=60,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Masterarbeit",
                        text="The Masterarbeit with accompanying colloquium counts as 30 LP.",
                        minimum=30,
                        maximum=30,
                        unit="LP",
                    ),
                ],
                related_issue_codes=["module_area_lp_total", "master_thesis_lp"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="grundlagenbereich",
                title="Grundlagenbereich",
                description="All students must complete the following four mandatory modules (30 LP).",
                items=[_module_item(module) for module in GRUNDLAGEN_MODULES],
                related_issue_codes=["grundlagen_incomplete"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="profile-choice",
                title="Profile Choice",
                description=(
                    "Students must choose and complete exactly one of two profiles: Data Science in "
                    "Life Sciences or Data Science Technologies. The chosen profile is determined by "
                    "taking the corresponding mandatory modules. Profile elective modules must not be "
                    "identical to modules already completed in the Bachelor's degree; in doubtful "
                    "cases the Prüfungsausschuss decides."
                ),
                items=[
                    ProgramRuleItem(
                        label="Exactly one profile",
                        text="Complete either Data Science in Life Sciences or Data Science Technologies (60 LP).",
                    ),
                    ProgramRuleItem(
                        label="No Bachelor duplicates",
                        text="Profile elective modules must not repeat modules from the Bachelor's degree.",
                    ),
                ],
                related_issue_codes=["profile_ambiguous", "profile_unclear", "duplicate_modules"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="profile-life-sciences",
                title="Profile: Data Science in Life Sciences",
                description=(
                    "60 LP total: 30 LP mandatory modules, 15 LP electives from the Life Sciences "
                    "profile list, and 15 LP electives from the other-profile (Technologies) list."
                ),
                items=[
                    *[_module_item(module) for module in LIFE_SCIENCES_MANDATORY_MODULES],
                    ProgramRuleItem(
                        label="Life Sciences electives",
                        text="15 LP from the Life Sciences profile elective list.",
                        minimum=15,
                        maximum=15,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Other-profile electives",
                        text="15 LP from the Technologies / other-profile elective list.",
                        minimum=15,
                        maximum=15,
                        unit="LP",
                    ),
                ],
                related_issue_codes=[
                    "profile_mandatory_missing",
                    "own_profile_electives_lp",
                    "other_profile_electives_lp",
                ],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="profile-technologies",
                title="Profile: Data Science Technologies",
                description=(
                    "60 LP total: 15 LP mandatory modules (Softwareprojekt Data Science A, Ethical "
                    "Foundations of Data Science), 30 LP electives from the Technologies profile "
                    "list, and 15 LP electives from the other-profile (Life Sciences) list."
                ),
                items=[
                    ProgramRuleItem(
                        label="Softwareprojekt Data Science A",
                        text="Softwareprojekt Data Science A (10 LP)",
                        minimum=10,
                        maximum=10,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Ethical Foundations of Data Science",
                        text="Ethical Foundations of Data Science (5 LP)",
                        minimum=5,
                        maximum=5,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Technologies electives",
                        text="30 LP from the Technologies profile elective list.",
                        minimum=30,
                        maximum=30,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Other-profile electives",
                        text="15 LP from the Life Sciences / other-profile elective list.",
                        minimum=15,
                        maximum=15,
                        unit="LP",
                    ),
                ],
                related_issue_codes=[
                    "profile_mandatory_missing",
                    "own_profile_electives_lp",
                    "other_profile_electives_lp",
                ],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="elective-pools",
                title="Elective Module Pools",
                description=(
                    "Eligible elective modules per pool. The interdisciplinary modules count only in "
                    "the other-profile elective sub-area of either profile. With Prüfungsausschuss "
                    "approval, up to 15 LP from other Master's programs may replace the other-profile "
                    "elective part."
                ),
                items=[
                    ProgramRuleItem(
                        label="Life Sciences pool",
                        text="; ".join(module.name for module in LIFE_SCIENCES_ELECTIVE_MODULES),
                    ),
                    ProgramRuleItem(
                        label="Technologies pool",
                        text="; ".join(module.name for module in TECHNOLOGIES_ELECTIVE_MODULES),
                    ),
                    ProgramRuleItem(
                        label="Interdisciplinary (other-profile only)",
                        text="; ".join(module.name for module in INTERDISCIPLINARY_MODULES),
                    ),
                    ProgramRuleItem(
                        label="External modules",
                        text=(
                            "Up to 15 LP from other Master's programs may replace the other-profile "
                            "elective part, only with Prüfungsausschuss approval."
                        ),
                        maximum=15,
                        unit="LP",
                    ),
                ],
                related_issue_codes=["unmatched_modules", "module_lp_mismatch"],
                sources=DEFAULT_SOURCES,
            ),
            ProgramRuleSection(
                id="masterarbeit",
                title="Masterarbeit",
                description=(
                    "The Masterarbeit (30 LP) includes an accompanying colloquium, normally one "
                    "approx. 30-minute talk on thesis progress. The topic area is Data Science, "
                    "length approx. 70 pages, working time 23 weeks. English is the default "
                    "language; German is possible only with an approved request. An external thesis "
                    "is possible with approval if academic supervision is ensured."
                ),
                items=[
                    ProgramRuleItem(
                        label="Masterarbeit LP",
                        text="30 LP including the accompanying colloquium.",
                        minimum=30,
                        maximum=30,
                        unit="LP",
                    ),
                    ProgramRuleItem(
                        label="Admission requirement",
                        text="At least 60 LP completed in the program before admission to the Masterarbeit.",
                        minimum=60,
                        unit="LP",
                    ),
                ],
                related_issue_codes=["master_thesis_lp", "thesis_admission_lp"],
                sources=DEFAULT_SOURCES,
            ),
        ],
    )
