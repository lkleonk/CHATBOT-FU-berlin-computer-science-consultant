import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.domain.study_plan import PlannedModule, StudyPlan, normalize_area
from app.settings import BACKEND_ROOT


CATALOG_PATH = BACKEND_ROOT / "knowledge_base" / "generated" / "module_catalog.json"


class ModuleRecord(BaseModel):
    name: str
    area: str
    lp: int
    is_ungraded: bool = False
    is_bachelor_module: bool = False
    is_scientific_work: bool = False
    is_software_project: bool = False


def normalize_module_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, ModuleRecord]:
    if not CATALOG_PATH.exists():
        return {}
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    records = [ModuleRecord.model_validate(item) for item in data]
    return {normalize_module_name(record.name): record for record in records}


def find_module(name: str) -> ModuleRecord | None:
    normalized = normalize_module_name(name)
    catalog = load_catalog()
    if normalized in catalog:
        return catalog[normalized]

    # Tolerate optional hyphen after "Softwareprojekt" in user input.
    relaxed = normalized.replace("softwareprojekt ", "softwareprojekt ")
    return catalog.get(relaxed)


def infer_area_from_name(name: str) -> str:
    normalized = normalize_module_name(name)
    if "praktische informatik" in normalized or "praktischen informatik" in normalized:
        return "practical"
    if "theoretische informatik" in normalized or "theoretischen informatik" in normalized:
        return "theoretical"
    if "technische informatik" in normalized or "technischen informatik" in normalized:
        return "technical"
    if "masterarbeit" in normalized:
        return "thesis"
    return "unknown"


def enrich_module(module: PlannedModule) -> PlannedModule:
    record = find_module(module.name)
    normalized_name = normalize_module_name(module.name)

    updates = {}
    if record is not None:
        updates["name"] = record.name
        if module.lp == 0:
            updates["lp"] = record.lp
        if module.area == "unknown":
            updates["area"] = normalize_area(record.area)
        updates["is_ungraded"] = module.is_ungraded or record.is_ungraded
        updates["is_bachelor_module"] = module.is_bachelor_module or record.is_bachelor_module
        updates["is_scientific_work"] = module.is_scientific_work or record.is_scientific_work
        updates["is_software_project"] = module.is_software_project or record.is_software_project
    else:
        inferred_area = infer_area_from_name(module.name)
        if module.area == "unknown" and inferred_area != "unknown":
            updates["area"] = inferred_area
        if "wahlbereich" in normalized_name:
            updates["is_wahlbereich"] = True
        if "wissenschaftliches arbeiten" in normalized_name:
            updates["is_scientific_work"] = True
            updates["is_ungraded"] = True
            if module.lp == 0:
                updates["lp"] = 5
        if "softwareprojekt" in normalized_name:
            updates["is_software_project"] = True
            if normalized_name.endswith(" b") or " b " in normalized_name:
                updates["is_ungraded"] = True
            if module.lp == 0:
                updates["lp"] = 10
        if "masterarbeit" in normalized_name and module.lp == 0:
            updates["lp"] = 30

    return module.model_copy(update=updates)


def enrich_study_plan(plan: StudyPlan) -> StudyPlan:
    return plan.model_copy(update={"modules": [enrich_module(module) for module in plan.modules]})
