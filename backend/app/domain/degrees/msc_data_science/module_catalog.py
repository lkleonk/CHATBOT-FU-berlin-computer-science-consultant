"""Canonical module catalogue for the M.Sc. Data Science (FU-Mitteilungen 18/2021).

Source: docs/data_science_master.md. Unlike the M.Sc. Informatik, this degree is
validated as a checklist against named modules, so the canonical lists live here
and the deterministic validator matches parsed module names against them.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.domain.module_catalog import normalize_module_name
from app.domain.study_plan import StudyPlan


@dataclass(frozen=True)
class CatalogModule:
    id: str
    name: str
    # None when the official LP value varies ("see module catalogue").
    lp: int | None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Profile:
    id: str
    display_name: str
    mandatory_ids: tuple[str, ...]
    # Modules unique to this profile's mandatory area; their presence marks the
    # profile as chosen (the order says the profile "is determined by taking
    # the corresponding mandatory modules").
    marker_ids: tuple[str, ...]
    own_elective_ids: tuple[str, ...]
    other_elective_ids: tuple[str, ...]
    own_elective_lp: int
    other_elective_lp: int


GRUNDLAGEN_MODULES = (
    CatalogModule("introduction_to_profile_areas", "Introduction to Profile Areas", 5),
    CatalogModule("statistics_for_data_science", "Statistics for Data Science", 10),
    CatalogModule(
        "machine_learning_for_data_science",
        "Machine Learning for Data Science",
        10,
        aliases=("ML for Data Science",),
    ),
    CatalogModule("programming_for_data_science", "Programming for Data Science", 5),
)

LIFE_SCIENCES_MANDATORY_MODULES = (
    CatalogModule("data_science_in_life_sciences", "Data Science in Life Sciences", 15),
    CatalogModule("forschungspraxis", "Forschungspraxis", 10, aliases=("Research Practice",)),
    CatalogModule("ethical_foundations_of_data_science", "Ethical Foundations of Data Science", 5),
)

TECHNOLOGIES_MANDATORY_MODULES = (
    CatalogModule(
        "softwareprojekt_data_science_a",
        "Softwareprojekt Data Science A",
        10,
        aliases=("Software Project Data Science A",),
    ),
    # Ethical Foundations is mandatory in both profiles; defined once above.
)

LIFE_SCIENCES_ELECTIVE_MODULES = (
    CatalogModule(
        "spezielle_aspekte_ds_life_sciences",
        "Spezielle Aspekte der Data Science in Life Sciences",
        5,
    ),
    CatalogModule(
        "aktuelle_forschungsthemen_ds_life_sciences",
        "Aktuelle Forschungsthemen der Data Science in Life Sciences",
        5,
    ),
    CatalogModule(
        "masterseminar_ds_life_sciences",
        "Masterseminar Data Science in Life Sciences",
        5,
    ),
    CatalogModule(
        "ausgewaehlte_themen_ds_life_sciences",
        "Ausgewählte Themen der Data Science in Life Sciences",
        10,
    ),
    CatalogModule("machine_learning_in_bioinformatics", "Machine Learning in Bioinformatics", 5),
    CatalogModule("big_data_analysis_in_bioinformatics", "Big Data Analysis in Bioinformatics", 5),
    CatalogModule(
        "applied_machine_learning_in_bioinformatics",
        "Applied Machine Learning in Bioinformatics",
        5,
    ),
)

TECHNOLOGIES_ELECTIVE_MODULES = (
    CatalogModule(
        "spezielle_aspekte_ds_technologies",
        "Spezielle Aspekte der Data Science Technologies",
        None,
    ),
    CatalogModule(
        "aktuelle_forschungsthemen_ds_technologies",
        "Aktuelle Forschungsthemen der Data Science Technologies",
        5,
    ),
    CatalogModule(
        "ausgewaehlte_themen_ds_technologies_a",
        "Ausgewählte Themen der Data Science Technologies A",
        10,
    ),
    CatalogModule(
        "ausgewaehlte_themen_ds_technologies_b",
        "Ausgewählte Themen der Data Science Technologies B",
        10,
    ),
    CatalogModule(
        "masterseminar_ds_technologies",
        "Masterseminar in Data Science Technologies",
        5,
        aliases=("Masterseminar Data Science Technologies",),
    ),
    CatalogModule(
        "softwareprojekt_data_science_b",
        "Softwareprojekt Data Science B",
        10,
        aliases=("Software Project Data Science B",),
    ),
    CatalogModule("datenbanksysteme_data_science", "Datenbanksysteme Data Science", 5),
    CatalogModule("verteilte_systeme", "Verteilte Systeme", 5, aliases=("Distributed Systems",)),
    CatalogModule("mobilkommunikation", "Mobilkommunikation", 5, aliases=("Mobile Communication",)),
    CatalogModule("telematik", "Telematik", 10, aliases=("Telematics",)),
    CatalogModule("hoehere_algorithmik", "Höhere Algorithmik", 10, aliases=("Advanced Algorithms",)),
    CatalogModule("rechnersicherheit", "Rechnersicherheit", 10, aliases=("Computer Security",)),
    CatalogModule("mustererkennung", "Mustererkennung", 5, aliases=("Pattern Recognition",)),
    CatalogModule(
        "netzbasierte_informationssysteme",
        "Netzbasierte Informationssysteme",
        5,
    ),
    CatalogModule("kuenstliche_intelligenz", "Künstliche Intelligenz", 5, aliases=("Artificial Intelligence",)),
    CatalogModule(
        "spezielle_aspekte_der_datenverwaltung",
        "Spezielle Aspekte der Datenverwaltung",
        5,
    ),
)

# Listed only in the "other-profile" elective sub-area of both profiles.
INTERDISCIPLINARY_MODULES = (
    CatalogModule(
        "interdisziplinaere_zugaenge_data_science_a",
        "Interdisziplinäre Zugänge im Rahmen von Data Science A",
        5,
    ),
    CatalogModule(
        "interdisziplinaere_zugaenge_data_science_b",
        "Interdisziplinäre Zugänge im Rahmen von Data Science B",
        10,
    ),
)

THESIS_MODULE = CatalogModule(
    "masterarbeit_data_science",
    "Masterarbeit mit begleitendem Kolloquium",
    30,
    aliases=("Masterarbeit", "Master Thesis", "Master's Thesis"),
)

ALL_MODULES: tuple[CatalogModule, ...] = (
    *GRUNDLAGEN_MODULES,
    *LIFE_SCIENCES_MANDATORY_MODULES,
    *TECHNOLOGIES_MANDATORY_MODULES,
    *LIFE_SCIENCES_ELECTIVE_MODULES,
    *TECHNOLOGIES_ELECTIVE_MODULES,
    *INTERDISCIPLINARY_MODULES,
    THESIS_MODULE,
)

GRUNDLAGEN_IDS = tuple(module.id for module in GRUNDLAGEN_MODULES)


def _ids(modules: tuple[CatalogModule, ...]) -> tuple[str, ...]:
    return tuple(module.id for module in modules)


PROFILES: dict[str, Profile] = {
    "life_sciences": Profile(
        id="life_sciences",
        display_name="Data Science in Life Sciences",
        mandatory_ids=_ids(LIFE_SCIENCES_MANDATORY_MODULES),
        marker_ids=("data_science_in_life_sciences", "forschungspraxis"),
        own_elective_ids=_ids(LIFE_SCIENCES_ELECTIVE_MODULES),
        other_elective_ids=_ids(TECHNOLOGIES_ELECTIVE_MODULES) + _ids(INTERDISCIPLINARY_MODULES),
        own_elective_lp=15,
        other_elective_lp=15,
    ),
    "technologies": Profile(
        id="technologies",
        display_name="Data Science Technologies",
        mandatory_ids=("softwareprojekt_data_science_a", "ethical_foundations_of_data_science"),
        marker_ids=("softwareprojekt_data_science_a",),
        own_elective_ids=_ids(TECHNOLOGIES_ELECTIVE_MODULES),
        other_elective_ids=_ids(LIFE_SCIENCES_ELECTIVE_MODULES) + _ids(INTERDISCIPLINARY_MODULES),
        own_elective_lp=30,
        other_elective_lp=15,
    ),
}


@lru_cache(maxsize=1)
def modules_by_id() -> dict[str, CatalogModule]:
    return {module.id: module for module in ALL_MODULES}


@lru_cache(maxsize=1)
def modules_by_normalized_name() -> dict[str, CatalogModule]:
    index: dict[str, CatalogModule] = {}
    for module in ALL_MODULES:
        for name in (module.name, *module.aliases):
            index[normalize_module_name(name)] = module
    return index


def find_module(name: str) -> CatalogModule | None:
    return modules_by_normalized_name().get(normalize_module_name(name))


def enrich_study_plan(plan: StudyPlan) -> StudyPlan:
    """Canonicalize matched module names and fill missing LP from the catalogue."""
    modules = []
    for module in plan.modules:
        record = find_module(module.name)
        updates = {}
        if record is not None:
            updates["name"] = record.name
            if module.lp == 0 and record.lp is not None:
                updates["lp"] = record.lp
            if record.id == THESIS_MODULE.id:
                updates["area"] = "thesis"
        modules.append(module.model_copy(update=updates))
    return plan.model_copy(update={"modules": modules})
