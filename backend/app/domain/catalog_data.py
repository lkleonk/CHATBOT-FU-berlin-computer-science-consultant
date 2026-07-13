"""Load canonical course records and degree-specific credit mappings."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_ROOT = Path(__file__).with_name("data")
COURSES_PATH = DATA_ROOT / "courses.json"
DEGREE_MODULES_DIR = DATA_ROOT / "degree_modules"
COURSE_OFFERINGS_DIR = DATA_ROOT / "course_offerings"


@lru_cache(maxsize=1)
def load_courses() -> dict[str, dict[str, Any]]:
    data = json.loads(COURSES_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("courses.json must contain a list of course records.")

    courses: dict[str, dict[str, Any]] = {}
    for index, course in enumerate(data):
        label = f"courses[{index}]"
        if not isinstance(course, dict):
            raise ValueError(f"{label} must be an object.")
        course_id = course.get("id")
        if not isinstance(course_id, str) or not course_id.strip():
            raise ValueError(f"{label}.id must be a non-empty string.")
        if course_id in courses:
            raise ValueError(f"courses.json duplicates course id {course_id!r}.")
        if not isinstance(course.get("name"), str) or not course["name"].strip():
            raise ValueError(f"{label}.name must be a non-empty string.")
        if course.get("lp") is not None and not isinstance(course["lp"], int):
            raise ValueError(f"{label}.lp must be an integer or null.")
        aliases = course.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias.strip() for alias in aliases):
            raise ValueError(f"{label}.aliases must be a list of non-empty strings.")
        courses[course_id] = course
    return courses


@lru_cache(maxsize=8)
def load_degree_module_data(degree_id: str) -> dict[str, Any]:
    path = DEGREE_MODULES_DIR / f"{degree_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
        raise ValueError(f"{path.name} must contain a modules list.")

    courses = load_courses()
    seen_ids: set[str] = set()
    for index, module in enumerate(data["modules"]):
        label = f"{path.name}.modules[{index}]"
        if not isinstance(module, dict):
            raise ValueError(f"{label} must be an object.")
        module_id = module.get("id")
        if not isinstance(module_id, str) or not module_id.strip():
            raise ValueError(f"{label}.id must be a non-empty string.")
        if module_id in seen_ids:
            raise ValueError(f"{path.name} duplicates module id {module_id!r}.")
        seen_ids.add(module_id)
        course_id = module.get("course_id")
        if course_id not in courses:
            raise ValueError(f"{label} references unknown course id {course_id!r}.")
    return data


def course_name(course_id: str) -> str:
    return str(load_courses()[course_id]["name"])


def course_lp(course_id: str) -> int | None:
    return load_courses()[course_id].get("lp")


def module_entries_by_id(degree_id: str) -> dict[str, dict[str, Any]]:
    return {
        str(module["id"]): module
        for module in load_degree_module_data(degree_id)["modules"]
    }


def module_names(degree_id: str) -> dict[str, str]:
    return {
        module_id: course_name(str(module["course_id"]))
        for module_id, module in module_entries_by_id(degree_id).items()
    }
