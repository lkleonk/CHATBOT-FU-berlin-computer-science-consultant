"""Project canonical course data into degree- and semester-specific lookups.

Course identity lives in ``data/courses.json``. Degree credit mappings live in
``data/degree_modules/<degree>.json`` and semester delivery details live in
``data/course_offerings/<semester>.json``. This keeps shared courses and their
LP values canonical while allowing a course to count differently per degree.
"""

import re
from functools import lru_cache
from typing import Any

from app.domain.catalog_data import (
    COURSE_OFFERINGS_DIR,
    course_name,
    load_courses,
    load_degree_module_data,
    module_entries_by_id,
)


LOOKUP_KEY_SEPARATOR = "/"
VALID_COURSE_TYPES = {"vl", "swp", "seminar"}
REQUIRED_OFFERING_FIELDS = {"course_id", "type", "lp", "schedule", "description", "url"}
MARKDOWN_LINK_RE = re.compile(r"^\[[^\]]+\]\((https?://[^)]+)\)$")
SEMESTER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def normalize_course_url(value: Any) -> str | None:
    if value is None or not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    markdown_match = MARKDOWN_LINK_RE.match(stripped)
    return markdown_match.group(1) if markdown_match else stripped


def load_course_entries() -> list[dict[str, Any]]:
    """Return flattened semester offerings enriched with canonical course names."""
    return _load_course_entries_cached()


@lru_cache(maxsize=1)
def _load_course_entries_cached() -> list[dict[str, Any]]:
    validate_course_catalog()
    entries: list[dict[str, Any]] = []
    for path in sorted(COURSE_OFFERINGS_DIR.glob("*.json")):
        data = _read_semester_file(path)
        semester = data["semester"]
        for offering in data["offerings"]:
            entries.append({"semester": semester, **offering, "title": course_name(offering["course_id"])})
    return entries


def _read_semester_file(path) -> dict[str, Any]:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain an object.")
    semester = data.get("semester")
    if not isinstance(semester, str) or not SEMESTER_RE.match(semester):
        raise ValueError(f"{path.name} has an invalid semester.")
    if path.stem != semester:
        raise ValueError(f"{path.name} must match its semester value {semester!r}.")
    offerings = data.get("offerings")
    if not isinstance(offerings, list) or not offerings:
        raise ValueError(f"{path.name}.offerings must be a non-empty list.")
    return data


def validate_course_catalog() -> None:
    """Validate the three-layer catalogue and all cross-file references."""
    from app.domain.degrees import get_degree, is_valid_degree, list_degrees

    courses = load_courses()
    if not COURSE_OFFERINGS_DIR.exists():
        raise ValueError("course_offerings directory is missing.")

    credit_maps: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for degree_summary in list_degrees():
        degree_id = degree_summary.id
        degree = get_degree(degree_id)
        data = load_degree_module_data(degree_id)
        modules = module_entries_by_id(degree_id)
        credit_map: dict[str, list[dict[str, Any]]] = {}

        for module_id, module in modules.items():
            area = module.get("area")
            if area is not None and area not in {*degree.course_areas, "thesis"}:
                raise ValueError(f"{degree_id} module {module_id!r} has invalid area {area!r}.")
            for flag in ("is_ungraded", "is_bachelor_module", "is_scientific_work", "is_software_project"):
                if flag in module and not isinstance(module[flag], bool):
                    raise ValueError(f"{degree_id} module {module_id!r} {flag} must be a boolean.")

        mappings = data.get("offering_credits", [])
        if not isinstance(mappings, list):
            raise ValueError(f"{degree_id}.offering_credits must be a list.")
        for mapping in mappings:
            if not isinstance(mapping, dict) or mapping.get("course_id") not in courses:
                raise ValueError(f"{degree_id} credit mapping references an unknown course.")
            course_id = mapping["course_id"]
            if course_id in credit_map:
                raise ValueError(f"{degree_id} duplicates credit mapping for course {course_id!r}.")
            placements = mapping.get("placements")
            if not isinstance(placements, list) or not placements:
                raise ValueError(f"{degree_id} credit mapping {course_id!r} needs placements.")
            seen_areas: set[str] = set()
            for placement in placements:
                if not isinstance(placement, dict) or placement.get("module_id") not in modules:
                    raise ValueError(f"{degree_id} credit mapping {course_id!r} references an unknown module.")
                module = modules[placement["module_id"]]
                area = placement.get("area", module.get("area"))
                if area not in degree.course_areas:
                    raise ValueError(f"{degree_id} credit mapping {course_id!r} has invalid area {area!r}.")
                if area in seen_areas:
                    raise ValueError(f"{degree_id} credit mapping {course_id!r} places area {area!r} twice.")
                seen_areas.add(area)
                if placement.get("lp") is not None and not isinstance(placement["lp"], int):
                    raise ValueError(f"{degree_id} credit mapping {course_id!r} lp must be an integer or null.")
                if "is_bachelor_module" in placement and not isinstance(placement["is_bachelor_module"], bool):
                    raise ValueError(f"{degree_id} credit mapping {course_id!r} is_bachelor_module must be a boolean.")
            credit_map[course_id] = placements
        credit_maps[degree_id] = credit_map

    seen_entries: set[tuple[str, str, str]] = set()
    for path in sorted(COURSE_OFFERINGS_DIR.glob("*.json")):
        data = _read_semester_file(path)
        semester = data["semester"]
        for index, offering in enumerate(data["offerings"]):
            label = f"{path.name}.offerings[{index}]"
            if not isinstance(offering, dict):
                raise ValueError(f"{label} must be an object.")
            missing = REQUIRED_OFFERING_FIELDS - set(offering)
            if missing:
                raise ValueError(f"{label} misses required fields: {sorted(missing)}")
            extra = set(offering) - REQUIRED_OFFERING_FIELDS
            if extra:
                raise ValueError(f"{label} has unsupported fields: {sorted(extra)}")
            course_id = offering["course_id"]
            if course_id not in courses:
                raise ValueError(f"{label} references unknown course id {course_id!r}.")
            if offering.get("type") not in VALID_COURSE_TYPES:
                raise ValueError(f"{label} has invalid course type {offering.get('type')!r}.")
            if offering.get("lp") is not None and not isinstance(offering["lp"], int):
                raise ValueError(f"{label}.lp must be an integer or null.")
            for field in ("schedule", "description", "url"):
                if offering.get(field) is not None and not isinstance(offering[field], str):
                    raise ValueError(f"{label}.{field} must be a string or null.")
            identity = (semester, offering["type"], course_id)
            if identity in seen_entries:
                raise ValueError(f"{label} duplicates {identity}.")
            seen_entries.add(identity)


def _degree_placements(degree_id: str, course_id: str) -> list[dict[str, Any]]:
    data = load_degree_module_data(degree_id)
    for mapping in data.get("offering_credits", []):
        if mapping["course_id"] == course_id:
            return mapping["placements"]
    return []


def project_offerings(degree_id: str) -> dict[str, Any]:
    return _project_offerings_cached(degree_id)


@lru_cache(maxsize=8)
def _project_offerings_cached(degree_id: str) -> dict[str, Any]:
    from app.domain.degrees import get_degree

    degree = get_degree(degree_id)
    modules = module_entries_by_id(degree_id)
    tree: dict[str, Any] = {}
    for offering in load_course_entries():
        for placement in _degree_placements(degree_id, offering["course_id"]):
            module = modules[placement["module_id"]]
            area = placement.get("area", module.get("area"))
            course = {
                "title": offering["title"],
                "module_catalog_name": degree.course_modules[placement["module_id"]],
                "lp": placement.get("lp") if placement.get("lp") is not None else offering.get("lp"),
                "schedule": offering.get("schedule"),
                "description": offering.get("description"),
                "url": offering.get("url"),
            }
            if placement.get("is_bachelor_module") or module.get("is_bachelor_module"):
                course["is_bachelor_module"] = True
            bucket = tree.setdefault(offering["semester"], {}).setdefault(area, {}).setdefault(offering["type"], [])
            bucket.append(course)
    return tree


def has_offerings(degree_id: str) -> bool:
    return bool(project_offerings(degree_id))


def lookup_key(semester: str, area: str, course_type: str) -> str:
    return LOOKUP_KEY_SEPARATOR.join([semester, area, course_type])


def parse_lookup_key(key: str) -> tuple[str, str, str]:
    parts = key.split(LOOKUP_KEY_SEPARATOR)
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Lookup key must use semester/area/course_type format: {key!r}")
    return parts[0], parts[1], parts[2]


def iter_lookup_keys(degree_id: str) -> list[str]:
    return [
        lookup_key(semester, area, course_type)
        for semester, areas in project_offerings(degree_id).items()
        for area, course_types in areas.items()
        for course_type in course_types
    ]


def available_semesters(degree_id: str) -> list[str]:
    return list(project_offerings(degree_id).keys())


def build_available_semesters_note(degree_id: str) -> str:
    semesters = available_semesters(degree_id)
    if not semesters:
        return "Available semesters in local course-offering data: none."
    return (
        "Available semesters in local course-offering data: "
        f"{', '.join(semesters)}. No local course-offering data exists for other semesters."
    )


def available_areas(degree_id: str, semester: str) -> list[str]:
    return list((project_offerings(degree_id).get(semester) or {}).keys())


def available_course_types(degree_id: str, semester: str, area: str) -> list[str]:
    return list(((project_offerings(degree_id).get(semester) or {}).get(area) or {}).keys())


def get_course_bucket(degree_id: str, key: str) -> dict[str, Any] | None:
    semester, area, course_type = parse_lookup_key(key)
    courses = ((project_offerings(degree_id).get(semester) or {}).get(area) or {}).get(course_type)
    if courses is None:
        return None
    return {"key": key, "semester": semester, "area": area, "course_type": course_type, "courses": [_normalized_course(course) for course in courses]}


def lookup_course_buckets(degree_id: str, keys: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    buckets: list[dict[str, Any]] = []
    invalid_keys: list[str] = []
    for key in dict.fromkeys(keys):
        try:
            bucket = get_course_bucket(degree_id, key)
        except ValueError:
            bucket = None
        if bucket is None:
            invalid_keys.append(key)
        else:
            buckets.append(bucket)
    return buckets, invalid_keys


def build_course_lookup_tree(degree_id: str) -> str:
    lines = ["Available course-offering lookup tree. Only output keys shown after ->."]
    for semester, areas in project_offerings(degree_id).items():
        lines.append(semester)
        for area, course_types in areas.items():
            lines.append(f"  {area}")
            for course_type, courses in course_types.items():
                key = lookup_key(semester, area, course_type)
                sample_titles = [str(course["title"]).strip() for course in courses[:3] if str(course["title"]).strip()]
                sample = f": {', '.join(sample_titles)}" if sample_titles else ""
                lines.append(f"    {course_type} -> {key} ({len(courses)} course(s){sample})")
    return "\n".join(lines)


def format_course_lookup_context(buckets: list[dict[str, Any]], invalid_keys: list[str] | None = None, notes: list[str] | None = None) -> str:
    parts = ["Exact local course offerings from the canonical course catalogue and semester data."]
    parts.extend(f"Note: {note}" for note in notes or [] if note)
    if invalid_keys:
        parts.append("No local course-offering bucket exists for these requested keys: " + ", ".join(invalid_keys))
    for bucket in buckets:
        lines = [
            f"## {bucket['key']}", f"Semester: {bucket['semester']}", f"Area: {bucket['area']}",
            f"Course type: {bucket['course_type']}", f"Grading hint: {_grading_hint(bucket['course_type'])}",
            f"Courses listed: {len(bucket['courses'])}",
        ]
        for index, course in enumerate(bucket["courses"], start=1):
            lines.extend(_format_course(index, course))
        parts.append("\n".join(lines))
    return "" if len(parts) == 1 else "\n\n".join(parts)


def build_course_citations(buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for bucket in buckets:
        source = f"backend/app/domain/data/course_offerings/{bucket['semester']}.json"
        _append_unique_citation(citations, seen, {"source": source, "title": "Course offerings", "section_heading": bucket["key"], "page": None, "score": 1.0})
        for course in bucket["courses"]:
            url = normalize_course_url(course.get("url"))
            if url:
                _append_unique_citation(citations, seen, {"source": url, "title": course.get("title"), "section_heading": bucket["key"], "page": None, "score": 1.0})
    return citations


def _append_unique_citation(citations: list[dict[str, Any]], seen: set[tuple[str, str | None, str | None]], citation: dict[str, Any]) -> None:
    identity = (citation["source"], citation.get("title"), citation.get("section_heading"))
    if identity not in seen:
        seen.add(identity)
        citations.append(citation)


def _normalized_course(course: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(course)
    normalized["url"] = normalize_course_url(course.get("url"))
    return normalized


def _format_course(index: int, course: dict[str, Any]) -> list[str]:
    lp = course.get("lp") if course.get("lp") is not None else "not listed in offerings data"
    lines = [f"{index}. Title: {course.get('title')}", f"   Module catalog name: {course.get('module_catalog_name')}", f"   LP: {lp}"]
    if course.get("is_bachelor_module"):
        lines.append("   Bachelor module: counts toward the maximum of 15 LP of Bachelor modules in a Master plan.")
    if course.get("schedule"):
        lines.append(f"   Schedule: {course['schedule']}")
    if course.get("description"):
        lines.append(f"   Description: {course['description']}")
    if course.get("url"):
        lines.append(f"   URL: {course['url']}")
    return lines


def _grading_hint(course_type: str) -> str:
    if course_type == "vl":
        return "Vorlesung module; treat as graded for advisory answers."
    if course_type == "seminar":
        return "Seminar/Wissenschaftliches Arbeiten; treat as ungraded for advisory answers."
    if course_type == "swp":
        return "Softwareprojekt A is graded and Softwareprojekt B is ungraded; use the module catalog name when present."
    return "No grading hint available."
