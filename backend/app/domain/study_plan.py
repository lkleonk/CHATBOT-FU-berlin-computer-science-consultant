from typing import Literal

from pydantic import BaseModel, Field, field_validator


Area = Literal["practical", "theoretical", "technical", "application", "thesis", "unknown"]
SpecializationArea = Literal["practical", "theoretical", "technical"]


AREA_ALIASES = {
    "practical": "practical",
    "praktisch": "practical",
    "praktische informatik": "practical",
    "theoretical": "theoretical",
    "theoretisch": "theoretical",
    "theoretische informatik": "theoretical",
    "technical": "technical",
    "technisch": "technical",
    "technische informatik": "technical",
    "application": "application",
    "anwendungsbereich": "application",
    "nebenfach": "application",
    "thesis": "thesis",
    "masterarbeit": "thesis",
    "unknown": "unknown",
    "": "unknown",
}


def normalize_area(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    return AREA_ALIASES.get(text, text if text in AREA_ALIASES.values() else "unknown")


class PlannedModule(BaseModel):
    name: str
    lp: int = Field(default=0, ge=0)
    area: Area = "unknown"
    is_wahlbereich: bool = False
    is_ungraded: bool = False
    is_bachelor_module: bool = False
    is_scientific_work: bool = False
    is_software_project: bool = False

    @field_validator("area", mode="before")
    @classmethod
    def coerce_area(cls, value: object) -> str:
        return normalize_area(value)


class StudyPlan(BaseModel):
    specialization_area: SpecializationArea | None = None
    modules: list[PlannedModule] = Field(default_factory=list)

    @field_validator("specialization_area", mode="before")
    @classmethod
    def coerce_specialization_area(cls, value: object) -> str | None:
        normalized = normalize_area(value)
        if normalized in {"practical", "theoretical", "technical"}:
            return normalized
        return None
