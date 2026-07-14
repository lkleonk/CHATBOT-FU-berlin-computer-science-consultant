from functools import lru_cache

from app.domain.program_rules import (
    ProgramRuleItem,
    ProgramRuleSection,
    ProgramRuleSource,
    ProgramRulesCatalogue,
)


STUDY_REGULATIONS = ProgramRuleSource(
    label="B.Sc. Informatik Studien- und Pruefungsordnung 2023 (FU-Mitteilungen 23/2023)",
    path="https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2023/ab232023.pdf",
)
ABV_REGULATIONS = ProgramRuleSource(
    label="Allgemeine ABV Studien- und Pruefungsordnung 2023 (FU-Mitteilungen 33/2023)",
    path="https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2023/ab332023.pdf",
)
ABV_AMENDMENT = ProgramRuleSource(
    label="ABV amendment 2025 (FU-Mitteilungen 05/2025)",
    path="https://www.fu-berlin.de/service/zuvdocs/amtsblatt/2025/ab052025.pdf",
)

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

CORE_MODULES = (
    ("Konzepte der Programmierung", 9),
    ("Diskrete Strukturen für Informatik", 9),
    ("Auswirkungen der Informatik", 6),
    ("Algorithmen und Datenstrukturen", 9),
    ("Lineare Algebra für Informatik", 9),
    ("Rechnerarchitektur", 6),
    ("Grundlagen der Theoretischen Informatik", 6),
    ("Nebenläufige, parallele und verteilte Programmierung", 9),
    ("Analysis für Informatik", 9),
    ("Betriebs- und Kommunikationssysteme", 6),
    ("Datenbanksysteme", 6),
    ("Programmierpraktikum", 5),
    ("Statistik für Informatik", 6),
    ("Informationssicherheit", 6),
    ("Softwaretechnik", 9),
    ("Wissenschaftliches Arbeiten in der Informatik", 6),
)

COMPULSORY_ELECTIVE_MODULES = (
    "Angewandte Biometrie",
    "Architektur eingebetteter Systeme",
    "Datenvisualisierung",
    "Forschungspraktikum",
    "Funktionale Programmierung",
    "Informationstheorie",
    "Maschinelles Lernen",
    "Mensch-Computer Interaktion",
    "Praktiken professioneller Softwareentwicklung",
    "Grundlagen des Datenschutzrechts",
    "Vertiefung Theoretische Informatik",
    "Aktuelle Themen in der Informatik",
    "Vertiefte Aspekte der Informatik",
)


def _module_item(name: str, lp: int) -> ProgramRuleItem:
    return ProgramRuleItem(label=name, text=f"{name} ({lp} LP)", minimum=lp, maximum=lp, unit="LP")


@lru_cache(maxsize=1)
def get_program_rules() -> ProgramRulesCatalogue:
    return ProgramRulesCatalogue(
        degree_program="FU Berlin B.Sc. Informatik",
        regulation="2023 study and examination regulations (FU-Mitteilungen 23/2023)",
        catalogue_version="bsc-informatik-2023-v1",
        source_note=(
            "Rules catalogue for the FU Berlin B.Sc. Informatik 2023 regulations. It covers the "
            "degree requirements only; local course-offering data and deterministic plan checking "
            "will be added with the canonical module catalogue. Official FU documents remain authoritative."
        ),
        sections=[
            ProgramRuleSection(
                id="overall-structure",
                title="Overall Structure",
                description=(
                    "The degree comprises 180 LP over a standard duration of six semesters: 150 LP "
                    "in Informatik, including the Bachelorarbeit, plus 30 LP Allgemeine Berufsvorbereitung (ABV)."
                ),
                items=[
                    ProgramRuleItem(label="Total degree volume", text="180 LP total.", minimum=180, maximum=180, unit="LP"),
                    ProgramRuleItem(label="Informatik", text="150 LP, including the Bachelorarbeit.", minimum=150, maximum=150, unit="LP"),
                    ProgramRuleItem(label="ABV", text="30 LP Allgemeine Berufsvorbereitung.", minimum=30, maximum=30, unit="LP"),
                ],
                sources=[STUDY_REGULATIONS],
            ),
            ProgramRuleSection(
                id="informatics-structure",
                title="Informatik Degree Area",
                description="The 150 LP Informatik area is divided into compulsory, compulsory-elective, free-elective, and thesis components.",
                items=[
                    ProgramRuleItem(label="Compulsory area", text="All listed compulsory modules.", minimum=116, maximum=116, unit="LP"),
                    ProgramRuleItem(label="Compulsory-elective area", text="Exactly two listed 6-LP modules.", minimum=12, maximum=12, unit="LP"),
                    ProgramRuleItem(label="Free-elective area", text="Scientific degree subjects that meaningfully supplement the degree.", minimum=10, maximum=10, unit="LP"),
                    ProgramRuleItem(label="Bachelorarbeit", text="Bachelorarbeit including presentation.", minimum=12, maximum=12, unit="LP"),
                ],
                sources=[STUDY_REGULATIONS],
            ),
            ProgramRuleSection(
                id="compulsory-modules",
                title="Compulsory Informatik Modules",
                description="All of these modules are mandatory and together total 116 LP.",
                items=[_module_item(name, lp) for name, lp in CORE_MODULES],
                sources=[STUDY_REGULATIONS],
            ),
            ProgramRuleSection(
                id="compulsory-elective-modules",
                title="Compulsory-Elective Modules",
                description="Complete exactly two distinct modules from this legally defined list; each counts as 6 LP.",
                items=[_module_item(name, 6) for name in COMPULSORY_ELECTIVE_MODULES],
                sources=[STUDY_REGULATIONS],
            ),
            ProgramRuleSection(
                id="free-elective-area",
                title="Free-Elective Area",
                description="Complete 10 LP from scientific degree subjects, which may include Informatik.",
                items=[
                    ProgramRuleItem(label="Free-elective volume", text="10 LP from suitable scientific degree subjects.", minimum=10, maximum=10, unit="LP"),
                    ProgramRuleItem(label="No double counting", text="Modules already counted in the compulsory or compulsory-elective area cannot be counted again."),
                    ProgramRuleItem(label="Meaningful supplement", text="The chosen modules must meaningfully supplement the qualification acquired in the degree."),
                    ProgramRuleItem(label="Advising", text="Subject advising before selecting these modules is formally recommended."),
                ],
                sources=[STUDY_REGULATIONS],
            ),
            ProgramRuleSection(
                id="abv",
                title="Allgemeine Berufsvorbereitung (ABV)",
                description=(
                    "The 30-LP ABV area includes the compulsory Softwareprojekt and a compulsory "
                    "professional internship. Additional eligible ABV competence modules fill the remaining LP."
                ),
                items=[
                    ProgramRuleItem(label="ABV total", text="30 LP in total.", minimum=30, maximum=30, unit="LP"),
                    ProgramRuleItem(label="Softwareprojekt", text="Compulsory Fachnahe Zusatzqualifikation module.", minimum=10, maximum=10, unit="LP"),
                    ProgramRuleItem(label="Internship", text="A Berufspraktikum is compulsory. Valid sizes are 5, 10, 15, or 20 LP; 20 LP must be an Auslandspraktikumsmodul."),
                    ProgramRuleItem(label="Recommended internship module", text="Berufsbezogenes Praktikum Informatik (10 LP) is strongly recommended, but is not the only valid internship route."),
                    ProgramRuleItem(label="Competence-area cap", text="Normally no more than 15 LP may be counted in one ABV competence area. Softwareprojekt contributes 10 LP to Fachnahe Zusatzqualifikationen."),
                    ProgramRuleItem(label="No content overlap", text="ABV work must not overlap in content with modules counted in the Informatik degree area or free-elective area."),
                ],
                sources=[STUDY_REGULATIONS, ABV_REGULATIONS, ABV_AMENDMENT],
            ),
            ProgramRuleSection(
                id="cross-university-courses",
                title="Courses at HU Berlin and TU Berlin (Nebenhörerschaft)",
                description=(
                    "Modules taken as a cross-registered student ('Nebenhörer:in', also called "
                    "Zweithörerschaft) at Humboldt-Universität or Technische Universität Berlin can be "
                    "recognized for the B.Sc. Informatik, most directly in the Free-Elective Area, and "
                    "in some cases as a specific compulsory-elective or ABV module. The steps below "
                    "describe the practical process."
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
                            "course could be credited. As of July 2026 this is Prof. Dr.-Ing. Volker "
                            "Roth (volker.roth@fu-berlin.de; see his "
                            "[contact page](https://www.mi.fu-berlin.de/inf/groups/ag-si/members/volkerroth.html) "
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
                            "B SPO §10(14)) on the "
                            "[Prüfungsausschuss Informatik page](https://www.mi.fu-berlin.de/w/Inf/PruefungsAusschuss) - "
                            "and then book an in-person appointment with the "
                            "Prüfungsausschussvorsitzende:r to explain why you took the course and how "
                            "it should count. Bring the Leistungsnachweis and the HU/TU module "
                            "description (Modulbeschreibung)."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Free-elective recognition",
                        text=(
                            "Courses in a scientific subject that meaningfully supplement the degree fit "
                            "the Free-Elective Area (10 LP) without needing to match an existing FU "
                            "module."
                        ),
                    ),
                    ProgramRuleItem(
                        label="Compulsory-elective equivalence",
                        text=(
                            "If a HU/TU course substantially matches one of the compulsory-elective "
                            "modules on the legally defined list ('passt in eine Modulhülle'), the "
                            "Prüfungsausschuss can recognize it as that module instead, counting toward "
                            "the 12 LP compulsory-elective area."
                        ),
                    ),
                    ProgramRuleItem(
                        label="ABV recognition",
                        text=(
                            "Suitable HU/TU courses may also be recognized within ABV competence areas, "
                            "subject to the same no-content-overlap rule as other ABV modules."
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
                id="bachelorarbeit",
                title="Bachelorarbeit",
                description="The Bachelorarbeit, including its presentation and discussion, counts as 12 LP.",
                items=[
                    ProgramRuleItem(label="Admission", text="At least 90 successfully completed LP and Wissenschaftliches Arbeiten in der Informatik successfully completed. Only passed or formally recognised credits establish eligibility."),
                    ProgramRuleItem(label="Topic", text="The topic must be from Informatik."),
                    ProgramRuleItem(label="Working time", text="12 weeks."),
                    ProgramRuleItem(label="Expected length", text="Approximately 7,500 words."),
                    ProgramRuleItem(label="Language", text="German or English; another language requires approval."),
                    ProgramRuleItem(label="Presentation", text="Approximately 15-minute presentation plus 15-minute discussion; it is part of the 12-LP component and is not separately graded."),
                    ProgramRuleItem(label="Passing requirement", text="The written thesis must receive at least grade 4.0."),
                ],
                sources=[STUDY_REGULATIONS],
            ),
        ],
    )
