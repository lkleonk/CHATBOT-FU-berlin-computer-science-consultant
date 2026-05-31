import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


COURSE_OFFERINGS_PATH = Path(__file__).with_name("data") / "course_offerings.json"
LOOKUP_KEY_SEPARATOR = "/"

VALID_AREAS = {"practical", "technical", "theoretical", "application"}
VALID_COURSE_TYPES = {"vl", "swp", "seminar"}
REQUIRED_COURSE_FIELDS = {"title", "module_catalog_name", "lp", "schedule", "description", "url"}
ALLOWED_COURSE_FIELDS = REQUIRED_COURSE_FIELDS

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


def load_course_offerings() -> dict[str, Any]:
    return _load_course_offerings_cached()


@lru_cache(maxsize=1)
def _load_course_offerings_cached() -> dict[str, Any]:
    data = json.loads(COURSE_OFFERINGS_PATH.read_text(encoding="utf-8"))
    validate_course_offerings(data)
    return data


def validate_course_offerings(data: Any) -> None:
    if not isinstance(data, dict) or not data:
        raise ValueError("Course offerings data must be a non-empty object.")

    for semester, areas in data.items():
        if not isinstance(semester, str) or not SEMESTER_RE.match(semester):
            raise ValueError(f"Invalid semester key: {semester!r}")
        if not isinstance(areas, dict) or not areas:
            raise ValueError(f"Semester {semester!r} must contain area objects.")

        for area, course_types in areas.items():
            if area not in VALID_AREAS:
                raise ValueError(f"Invalid area key {area!r} under {semester!r}.")
            if not isinstance(course_types, dict) or not course_types:
                raise ValueError(f"Area {semester}/{area} must contain course type lists.")

            for course_type, courses in course_types.items():
                if course_type not in VALID_COURSE_TYPES:
                    raise ValueError(f"Invalid course type key {course_type!r} under {semester}/{area}.")
                if not isinstance(courses, list):
                    raise ValueError(f"Bucket {semester}/{area}/{course_type} must be a list.")

                for index, course in enumerate(courses):
                    bucket = f"{semester}/{area}/{course_type}[{index}]"
                    _validate_course(course, bucket)


def _validate_course(course: Any, bucket: str) -> None:
    if not isinstance(course, dict):
        raise ValueError(f"Course entry {bucket} must be an object.")

    missing = REQUIRED_COURSE_FIELDS - set(course)
    if missing:
        raise ValueError(f"Course entry {bucket} misses required fields: {sorted(missing)}")

    extra = set(course) - ALLOWED_COURSE_FIELDS
    if extra:
        raise ValueError(f"Course entry {bucket} has unsupported fields: {sorted(extra)}")

    for field in ("title", "module_catalog_name"):
        if not isinstance(course.get(field), str) or not course[field].strip():
            raise ValueError(f"Course entry {bucket}.{field} must be a non-empty string.")

    if course.get("lp") is not None and not isinstance(course.get("lp"), int):
        raise ValueError(f"Course entry {bucket}.lp must be an integer or null.")

    for field in ("schedule", "description", "url"):
        if course.get(field) is not None and not isinstance(course.get(field), str):
            raise ValueError(f"Course entry {bucket}.{field} must be a string or null.")


def lookup_key(semester: str, area: str, course_type: str) -> str:
    return LOOKUP_KEY_SEPARATOR.join([semester, area, course_type])


def parse_lookup_key(key: str) -> tuple[str, str, str]:
    parts = key.split(LOOKUP_KEY_SEPARATOR)
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Lookup key must use semester/area/course_type format: {key!r}")
    return parts[0], parts[1], parts[2]


def iter_lookup_keys(offerings: dict[str, Any] | None = None) -> list[str]:
    data = offerings or load_course_offerings()
    keys: list[str] = []
    for semester, areas in data.items():
        for area, course_types in areas.items():
            for course_type in course_types:
                keys.append(lookup_key(semester, area, course_type))
    return keys


def available_semesters(offerings: dict[str, Any] | None = None) -> list[str]:
    return list((offerings or load_course_offerings()).keys())


def build_available_semesters_note(offerings: dict[str, Any] | None = None) -> str:
    semesters = available_semesters(offerings)
    if not semesters:
        return "Available semesters in local course-offering data: none."
    return (
        "Available semesters in local course-offering data: "
        f"{', '.join(semesters)}. "
        "No local course-offering data exists for other semesters."
    )


def available_areas(semester: str, offerings: dict[str, Any] | None = None) -> list[str]:
    data = offerings or load_course_offerings()
    return list((data.get(semester) or {}).keys())


def available_course_types(
    semester: str,
    area: str,
    offerings: dict[str, Any] | None = None,
) -> list[str]:
    data = offerings or load_course_offerings()
    return list(((data.get(semester) or {}).get(area) or {}).keys())


def get_course_bucket(key: str, offerings: dict[str, Any] | None = None) -> dict[str, Any] | None:
    semester, area, course_type = parse_lookup_key(key)
    data = offerings or load_course_offerings()
    courses = ((data.get(semester) or {}).get(area) or {}).get(course_type)
    if courses is None:
        return None

    return {
        "key": key,
        "semester": semester,
        "area": area,
        "course_type": course_type,
        "courses": [_normalized_course(course) for course in courses],
    }


def lookup_course_buckets(keys: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    buckets: list[dict[str, Any]] = []
    invalid_keys: list[str] = []
    seen: set[str] = set()

    for key in keys:
        if key in seen:
            continue
        seen.add(key)

        try:
            bucket = get_course_bucket(key)
        except ValueError:
            bucket = None

        if bucket is None:
            invalid_keys.append(key)
            continue

        buckets.append(bucket)

    return buckets, invalid_keys


def build_course_lookup_tree(offerings: dict[str, Any] | None = None) -> str:
    data = offerings or load_course_offerings()
    lines = ["Available course-offering lookup tree. Only output keys shown after ->."]

    for semester, areas in data.items():
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
