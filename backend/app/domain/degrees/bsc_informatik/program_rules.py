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
