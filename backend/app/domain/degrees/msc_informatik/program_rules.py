from functools import lru_cache

from app.domain.program_rules import (
    ProgramRuleItem,
    ProgramRuleSection,
    ProgramRuleSource,
    ProgramRulesCatalogue,
)


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

CROSS_UNIVERSITY_SOURCES = [
    ProgramRuleSource(
        label="HU Berlin Gast- und Nebenhoererschaft",
        path="https://www.hu-berlin.de/studium/nach-dem-studium/lebenslanges-lernen/gasthoerer-und-nebenhoererschaft",
    ),
    ProgramRuleSource(
        label="TU Berlin Gast- und Nebenhoererschaft",
        path="https://www.tu.berlin/studierendensekretariat/themen-a-z/gast-und-nebenhoererschaft/",
    ),
    ProgramRuleSource(
        label="Pruefungsausschuss Informatik (Anrechnung von Leistungen)",
        path="https://www.mi.fu-berlin.de/w/Inf/PruefungsAusschuss",
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
                id="cross-university-courses",
                title="Courses at HU Berlin and TU Berlin (Nebenhörerschaft)",
                description=(
                    "Modules taken as a cross-registered student ('Nebenhörer:in', also called "
                    "Zweithörerschaft) at Humboldt-Universität or Technische Universität Berlin can be "
                    "recognized for the Master Informatik, either as general area credit or, when "
                    "content matches, as a specific FU module. The steps below describe the practical "
                    "process."
                ),
                items=[
                    ProgramRuleItem(
                        label="Legal basis",
                        text=(
                            "Berlin's universities (FU, HU, TU, UdK) allow students to attend and be "
                            "examined in individual courses at a partner university as a Nebenhörer:in, "
                            "in addition to normal enrollment at their home university."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Step 1 - Find a course",
                        text=(
                            "Browse the host university's Vorlesungsverzeichnis for a module that "
                            "interests you and fits your Stundenplan: the "
                            "[TU Berlin Moses Vorlesungsverzeichnis](https://moseskonto.tu-berlin.de/moses/verzeichnis/veranstaltungen/vkpl_stg.html) "
                            "or the [HU Berlin Agnes Vorlesungsverzeichnis](https://agnes.hu-berlin.de/lupo/rds?state=change&type=5&"
                            "moduleParameter=abstgvSearch&nextdir=change&next=search.vm&subdir=stg&clean=y&"
                            "category=curricula.search&navigationPosition=lectures%2Ccurriculaschedules&"
                            "breadcrumb=curriculaschedules&topitem=lectures&subitem=curriculaschedules) "
                            "(if the deep link is broken, start at [agnes.hu-berlin.de](https://agnes.hu-berlin.de/))."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Step 2 - Optional pre-check with the Prüfungsausschuss",
                        text=(
                            "Ask the Prüfungsausschussvorsitzende:r by email or in person whether the "
                            "course could be credited. As of July 2026 this is Prof. Dr. Claudia "
                            "Müller-Birn (clmb@inf.fu-berlin.de; see her "
                            "[contact page](https://www.mi.fu-berlin.de/en/inf/groups/hcc/members/professor/mueller-birn.html) "
                            "for details and appointment booking). "
                            "The chair may not have time or may decline to assess a course you have not "
                            "taken yet; trying first and then deciding is still recommended."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Step 3 - Ask the teacher",
                        text=(
                            "Email the teacher of the HU/TU module and ask whether you may participate "
                            "as Nebenhörer:in. Attach the filled Nebenhörer application form: the "
                            "[HU form (PDF)](https://www.hu-berlin.de/fileadmin/Mediathek/Zentrale_Seiten/Studium/Dokumente/Studium_Anmeldung_Gasthorerschaft_Nebenhoererschaft_20210323.pdf) "
                            "or the [TU form (PDF)](https://www.static.tu.berlin/fileadmin/www/10002460/Bewerben_und_Einschreiben/GH_NH/Nebenhoererschein_SLM.pdf)."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Step 4 - Submit the Nebenhörer application",
                        text=(
                            "If the teacher agrees and signs, send the document to the responsible "
                            "office to validate the Nebenhörerantrag; the office is named on the form "
                            "and on the general information pages (see the "
                            "[HU Nebenhörerschaft page](https://www.hu-berlin.de/studium/nach-dem-studium/lebenslanges-lernen/gasthoerer-und-nebenhoererschaft) "
                            "and the [TU Nebenhörerschaft page](https://www.tu.berlin/studierendensekretariat/themen-a-z/gast-und-nebenhoererschaft/)). "
                            "The office can take time to answer - follow up by email if needed, and "
                            "attend the course from the start even while the confirmation is pending."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Taking the exam",
                        text=(
                            "Attend the course and sit the exam at the host university like one of its "
                            "own students; the host university issues a Leistungsnachweis with grade and "
                            "workload (LP or ECTS)."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Step 5 - Recognition at FU",
                        text=(
                            "At the end of the semester, register the recognition request online on the "
                            "[MVS platform](https://kvv.imp.fu-berlin.de/mvs2/) - the procedure is "
                            "explained under 'Anrechnung von Leistungen' (Anerkennung, RSPO §7, "
                            "M SPO §9(14)) on the "
                            "[Prüfungsausschuss Informatik page](https://www.mi.fu-berlin.de/w/Inf/PruefungsAusschuss) - "
                            "and then book an in-person appointment with the "
                            "Prüfungsausschussvorsitzende:r to explain why you took the course and how "
                            "it should count. Bring the Leistungsnachweis and the HU/TU module "
                            "description (Modulbeschreibung)."
                        ),
                    ),
                    ProgramRuleItem(
                        label="General-area recognition",
                        text=(
                            "Courses in a suitable scientific subject can be recognized directly in the "
                            "Anwendungsbereich (which is explicitly meant to draw on subjects outside "
                            "Informatik) or, with Prüfungsausschuss approval, in the Wahlbereich, without "
                            "needing to match an existing FU module title."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Module-equivalence recognition",
                        text=(
                            "If a HU/TU course's content and workload substantially match a specific "
                            "Informatik module ('passt in eine Modulhülle'), the Prüfungsausschuss can "
                            "instead recognize it as that module, so it counts toward the practical, "
                            "technical, or theoretical specialization areas rather than only "
                            "Anwendungsbereich or Wahlbereich."
                        ),
                    ),
                    ProgramRuleItem(
                        label="No double counting",
                        text=(
                            "Recognized external credit follows the same no-double-counting rule as FU "
                            "modules: the same content can only be counted once in the plan."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Links and contacts change",
                        text=(
                            "Chairs rotate and URLs move; if a link no longer works, start from the "
                            "HU/TU Nebenhörerschaft pages or the FU Informatik Prüfungsausschuss page. "
                            "The final recognition decision always lies with the Prüfungsausschuss."
                        ),
                    ),
                ],
                sources=CROSS_UNIVERSITY_SOURCES,
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
