"""Shared course-offerings dataset with per-degree projection.

``data/course_offerings.json`` is a flat list of offered courses. Each entry
appears once per semester and carries a ``degrees`` map tagging every degree
program it counts toward, with that degree's area classification(s):

    {
      "semester": "sose26",
      "type": "vl",
      "title": "Telematik",
      "lp": 10,
      "schedule": "...", "description": null, "url": "...",
      "degrees": {
        "msc_informatik": [
          {"area": "technical", "module_catalog_name": "Telematik"}
        ],
        "msc_data_science": [
          {"area": "technologies", "module_ids": ["telematik"]}
        ]
      }
    }

Placement rules (enforced at load time):
- ``area`` must belong to the degree's area vocabulary.
- Degrees with a canonical module list (``course_module_ids`` on the
  ``DegreeDefinition``) require ``module_ids`` (or ``module_id`` shorthand)
  referencing known ids; degrees without one require ``module_catalog_name``
  and must not carry module ids.
- ``lp`` inside a placement overrides the entry-level default for that degree.
- ``is_bachelor_module`` marks Bachelor lectures creditable in a Master
  (15 LP cap caveat).

Deterministic projection builds one ``semester -> area -> course_type``
bucket tree per degree; the LLM course-key selector only ever sees the tree
for the session's degree. The degree is never chosen by the LLM.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


COURSE_OFFERINGS_PATH = Path(__file__).with_name("data") / "course_offerings.json"
LOOKUP_KEY_SEPARATOR = "/"

VALID_COURSE_TYPES = {"vl", "swp", "seminar"}
REQUIRED_ENTRY_FIELDS = {"semester", "type", "title", "lp", "schedule", "description", "url", "degrees"}
ALLOWED_ENTRY_FIELDS = REQUIRED_ENTRY_FIELDS
ALLOWED_PLACEMENT_FIELDS = {"area", "module_catalog_name", "module_id", "module_ids", "lp", "is_bachelor_module"}

MARKDOWN_LINK_RE = re.compile(r"^\[[^\]]+\]\((https?://[^)]+)\)$")
SEMESTER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def normalize_course_url(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not stripped:
        return None

    markdown_match = MARKDOWN_LINK_RE.match(stripped)
    if markdown_match:
        return markdown_match.group(1)

    return stripped


def load_course_entries() -> list[dict[str, Any]]:
    return _load_course_entries_cached()


@lru_cache(maxsize=1)
def _load_course_entries_cached() -> list[dict[str, Any]]:
    data = json.loads(COURSE_OFFERINGS_PATH.read_text(encoding="utf-8"))
    validate_course_entries(data)
    return data


def validate_course_entries(data: Any) -> None:
    from app.domain.degrees import get_degree, is_valid_degree

    if not isinstance(data, list) or not data:
        raise ValueError("Course offerings data must be a non-empty list of course entries.")

    seen_identities: set[tuple[str, str, str]] = set()
    for index, entry in enumerate(data):
        label = f"entry[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{label} must be an object.")

        missing = REQUIRED_ENTRY_FIELDS - set(entry)
        if missing:
            raise ValueError(f"{label} misses required fields: {sorted(missing)}")
        extra = set(entry) - ALLOWED_ENTRY_FIELDS
        if extra:
            raise ValueError(f"{label} has unsupported fields: {sorted(extra)}")

        semester = entry.get("semester")
        if not isinstance(semester, str) or not SEMESTER_RE.match(semester):
            raise ValueError(f"{label} has an invalid semester: {semester!r}")
        if entry.get("type") not in VALID_COURSE_TYPES:
            raise ValueError(f"{label} has an invalid course type: {entry.get('type')!r}")
        if not isinstance(entry.get("title"), str) or not entry["title"].strip():
            raise ValueError(f"{label}.title must be a non-empty string.")
        if entry.get("lp") is not None and not isinstance(entry.get("lp"), int):
            raise ValueError(f"{label}.lp must be an integer or null.")
        for field in ("schedule", "description", "url"):
            if entry.get(field) is not None and not isinstance(entry.get(field), str):
                raise ValueError(f"{label}.{field} must be a string or null.")

        identity = (semester, entry["type"], entry["title"].strip())
        if identity in seen_identities:
            raise ValueError(
                f"{label} duplicates {identity}; a course appears once per semester "
                "with all degree tags on the same entry."
            )
        seen_identities.add(identity)

        degrees = entry.get("degrees")
        if not isinstance(degrees, dict) or not degrees:
            raise ValueError(f"{label}.degrees must be a non-empty object.")

        for degree_id, placements in degrees.items():
            if not is_valid_degree(degree_id):
                raise ValueError(f"{label} tags unknown degree id {degree_id!r}.")
            degree = get_degree(degree_id)

            if isinstance(placements, dict):
                placements = [placements]
            if not isinstance(placements, list) or not placements:
                raise ValueError(f"{label}.degrees.{degree_id} must be a placement object or list.")

            seen_areas: set[str] = set()
            for placement in placements:
                _validate_placement(placement, degree, f"{label}.degrees.{degree_id}")
                area = placement["area"]
                if area in seen_areas:
                    raise ValueError(f"{label}.degrees.{degree_id} places area {area!r} twice.")
                seen_areas.add(area)


def _validate_placement(placement: Any, degree, label: str) -> None:
    if not isinstance(placement, dict):
        raise ValueError(f"{label} placements must be objects.")

    extra = set(placement) - ALLOWED_PLACEMENT_FIELDS
    if extra:
        raise ValueError(f"{label} placement has unsupported fields: {sorted(extra)}")

    area = placement.get("area")
    if area not in degree.course_areas:
        raise ValueError(
            f"{label} placement area {area!r} is not in the degree's area vocabulary "
            f"{sorted(degree.course_areas)}."
        )

    if placement.get("lp") is not None and not isinstance(placement.get("lp"), int):
        raise ValueError(f"{label} placement lp must be an integer or null.")
    if not isinstance(placement.get("is_bachelor_module", False), bool):
        raise ValueError(f"{label} placement is_bachelor_module must be a boolean.")

    module_ids = _placement_module_ids(placement)
    if degree.course_modules is None:
        if module_ids:
            raise ValueError(
                f"{label} placement carries module ids, but the degree has no canonical module list."
            )
        name = placement.get("module_catalog_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"{label} placement requires a non-empty module_catalog_name.")
    else:
        if not module_ids:
            raise ValueError(
                f"{label} placement requires module_ids referencing the degree's canonical module list."
            )
        unknown = [module_id for module_id in module_ids if module_id not in degree.course_modules]
        if unknown:
            raise ValueError(f"{label} placement references unknown module ids: {unknown}")


def _placement_module_ids(placement: dict[str, Any]) -> list[str]:
    if "module_ids" in placement and "module_id" in placement:
        raise ValueError("A placement must use either module_id or module_ids, not both.")
    if "module_id" in placement:
        value = placement["module_id"]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("module_id must be a non-empty string.")
        return [value]
    value = placement.get("module_ids", [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError("module_ids must be a list of non-empty strings.")
    return value


def project_offerings(degree_id: str) -> dict[str, Any]:
    """Bucket tree ``semester -> area -> course_type -> [courses]`` for one degree."""
    return _project_offerings_cached(degree_id)


@lru_cache(maxsize=8)
def _project_offerings_cached(degree_id: str) -> dict[str, Any]:
    from app.domain.degrees import get_degree

    degree = get_degree(degree_id)
    tree: dict[str, Any] = {}

    for entry in load_course_entries():
        placements = entry["degrees"].get(degree_id)
        if placements is None:
            continue
        if isinstance(placements, dict):
            placements = [placements]

        for placement in placements:
            course = _projected_course(entry, placement, degree)
            bucket = (
                tree.setdefault(entry["semester"], {})
                .setdefault(placement["area"], {})
                .setdefault(entry["type"], [])
            )
            bucket.append(course)

    return tree


def _projected_course(entry: dict[str, Any], placement: dict[str, Any], degree) -> dict[str, Any]:
    module_ids = _placement_module_ids(placement)
    module_catalog_name = placement.get("module_catalog_name")
    if not module_catalog_name and module_ids and degree.course_modules:
        module_catalog_name = "; ".join(
            degree.course_modules.get(module_id, module_id) for module_id in module_ids
        )

    course = {
        "title": entry["title"],
        "module_catalog_name": module_catalog_name,
        "lp": placement.get("lp") if placement.get("lp") is not None else entry.get("lp"),
        "schedule": entry.get("schedule"),
        "description": entry.get("description"),
        "url": entry.get("url"),
    }
    if module_ids:
        course["module_ids"] = module_ids
    if placement.get("is_bachelor_module"):
        course["is_bachelor_module"] = True
    return course


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
    keys: list[str] = []
    for semester, areas in project_offerings(degree_id).items():
        for area, course_types in areas.items():
            for course_type in course_types:
                keys.append(lookup_key(semester, area, course_type))
    return keys


def available_semesters(degree_id: str) -> list[str]:
    return list(project_offerings(degree_id).keys())


def build_available_semesters_note(degree_id: str) -> str:
    semesters = available_semesters(degree_id)
    if not semesters:
        return "Available semesters in local course-offering data: none."
    return (
        "Available semesters in local course-offering data: "
        f"{', '.join(semesters)}. "
        "No local course-offering data exists for other semesters."
    )


def available_areas(degree_id: str, semester: str) -> list[str]:
    return list((project_offerings(degree_id).get(semester) or {}).keys())


def available_course_types(degree_id: str, semester: str, area: str) -> list[str]:
    tree = project_offerings(degree_id)
    return list(((tree.get(semester) or {}).get(area) or {}).keys())


def get_course_bucket(degree_id: str, key: str) -> dict[str, Any] | None:
    semester, area, course_type = parse_lookup_key(key)
    tree = project_offerings(degree_id)
    courses = ((tree.get(semester) or {}).get(area) or {}).get(course_type)
    if courses is None:
        return None

    return {
        "key": key,
        "semester": semester,
        "area": area,
        "course_type": course_type,
        "courses": [_normalized_course(course) for course in courses],
    }


def lookup_course_buckets(degree_id: str, keys: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    buckets: list[dict[str, Any]] = []
    invalid_keys: list[str] = []
    seen: set[str] = set()

    for key in keys:
        if key in seen:
            continue
        seen.add(key)

        try:
            bucket = get_course_bucket(degree_id, key)
        except ValueError:
            bucket = None

        if bucket is None:
            invalid_keys.append(key)
            continue

        buckets.append(bucket)

    return buckets, invalid_keys


def build_course_lookup_tree(degree_id: str) -> str:
    lines = ["Available course-offering lookup tree. Only output keys shown after ->."]

    for semester, areas in project_offerings(degree_id).items():
        lines.append(f"{semester}")
        for area, course_types in areas.items():
            lines.append(f"  {area}")
            for course_type, courses in course_types.items():
                key = lookup_key(semester, area, course_type)
                sample_titles = [
                    str(course.get("title", "")).strip()
                    for course in courses[:3]
                    if str(course.get("title", "")).strip()
                ]
                sample = f": {', '.join(sample_titles)}" if sample_titles else ""
                lines.append(f"    {course_type} -> {key} ({len(courses)} course(s){sample})")

    return "\n".join(lines)


def format_course_lookup_context(
    buckets: list[dict[str, Any]],
    invalid_keys: list[str] | None = None,
    notes: list[str] | None = None,
) -> str:
    parts = ["Exact local course offerings from backend/app/domain/data/course_offerings.json."]

    for note in notes or []:
        if note:
            parts.append(f"Note: {note}")

    if invalid_keys:
        parts.append(
            "No local course-offering bucket exists for these requested keys: "
            + ", ".join(invalid_keys)
        )

    for bucket in buckets:
        key = bucket["key"]
        course_type = bucket["course_type"]
        courses = bucket["courses"]
        lines = [
            f"## {key}",
            f"Semester: {bucket['semester']}",
            f"Area: {bucket['area']}",
            f"Course type: {course_type}",
            f"Grading hint: {_grading_hint(course_type)}",
            f"Courses listed: {len(courses)}",
        ]

        if not courses:
            lines.append("- No courses are listed in this bucket.")

        for index, course in enumerate(courses, start=1):
            lines.extend(_format_course(index, course))

        parts.append("\n".join(lines))

    if len(parts) == 1:
        return ""

    return "\n\n".join(parts)


def build_course_citations(buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str | None]] = set()

    for bucket in buckets:
        key = bucket["key"]
        bucket_citation = {
            "source": "backend/app/domain/data/course_offerings.json",
            "title": "Course offerings",
            "section_heading": key,
            "page": None,
            "score": 1.0,
        }
        _append_unique_citation(citations, seen, bucket_citation)

        for course in bucket["courses"]:
            url = normalize_course_url(course.get("url"))
            if not url:
                continue
            _append_unique_citation(
                citations,
                seen,
                {
                    "source": url,
                    "title": course.get("title"),
                    "section_heading": key,
                    "page": None,
                    "score": 1.0,
                },
            )

    return citations


def _append_unique_citation(
    citations: list[dict[str, Any]],
    seen: set[tuple[str, str | None, str | None]],
    citation: dict[str, Any],
) -> None:
    identity = (citation["source"], citation.get("title"), citation.get("section_heading"))
    if identity in seen:
        return
    seen.add(identity)
    citations.append(citation)


def _normalized_course(course: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(course)
    normalized["url"] = normalize_course_url(course.get("url"))
    return normalized


def _format_course(index: int, course: dict[str, Any]) -> list[str]:
    lp = course.get("lp") if course.get("lp") is not None else "not listed in offerings data"
    lines = [
        f"{index}. Title: {course.get('title')}",
        f"   Module catalog name: {course.get('module_catalog_name')}",
        f"   LP: {lp}",
    ]

    if course.get("is_bachelor_module"):
        lines.append(
            "   Bachelor module: counts toward the maximum of 15 LP of Bachelor modules in a Master plan."
        )
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
