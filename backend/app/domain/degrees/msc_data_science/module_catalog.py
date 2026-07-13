"""Canonical M.Sc. Data Science catalogue loaded from domain data."""

from dataclasses import dataclass
from functools import lru_cache

from app.domain.catalog_data import course_lp, course_name, load_degree_module_data
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
    marker_ids: tuple[str, ...]
    own_elective_ids: tuple[str, ...]
    other_elective_ids: tuple[str, ...]
    own_elective_lp: int
    other_elective_lp: int


_DATA = load_degree_module_data("msc_data_science")


def _catalog_module(entry: dict) -> CatalogModule:
    course_id = str(entry["course_id"])
    return CatalogModule(
        id=str(entry["id"]),
        name=course_name(course_id),
        lp=course_lp(course_id),
        aliases=tuple(entry.get("aliases", ())),
    )


ALL_MODULES: tuple[CatalogModule, ...] = tuple(_catalog_module(entry) for entry in _DATA["modules"])
_MODULES_BY_ID = {module.id: module for module in ALL_MODULES}
_GROUPS = _DATA["groups"]


def _modules(group: str) -> tuple[CatalogModule, ...]:
    return tuple(_MODULES_BY_ID[module_id] for module_id in _GROUPS[group])


GRUNDLAGEN_MODULES = _modules("grundlagen")
LIFE_SCIENCES_MANDATORY_MODULES = _modules("life_sciences_mandatory")
TECHNOLOGIES_MANDATORY_MODULES = _modules("technologies_mandatory")
LIFE_SCIENCES_ELECTIVE_MODULES = _modules("life_sciences_elective")
TECHNOLOGIES_ELECTIVE_MODULES = _modules("technologies_elective")
INTERDISCIPLINARY_MODULES = _modules("interdisciplinary")
THESIS_MODULE = _MODULES_BY_ID[str(_DATA["thesis_module_id"])]
GRUNDLAGEN_IDS = tuple(module.id for module in GRUNDLAGEN_MODULES)


def _profile(data: dict) -> Profile:
    return Profile(
        id=str(data["id"]),
        display_name=str(data["display_name"]),
        mandatory_ids=tuple(data["mandatory_ids"]),
        marker_ids=tuple(data["marker_ids"]),
        own_elective_ids=tuple(data["own_elective_ids"]),
        other_elective_ids=tuple(data["other_elective_ids"]),
        own_elective_lp=int(data["own_elective_lp"]),
        other_elective_lp=int(data["other_elective_lp"]),
    )


PROFILES = {profile_id: _profile(data) for profile_id, data in _DATA["profiles"].items()}


@lru_cache(maxsize=1)
def modules_by_id() -> dict[str, CatalogModule]:
    return dict(_MODULES_BY_ID)


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
