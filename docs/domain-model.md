# Domain Model

How degrees, course-offering data, and program rules fit together. Per-degree
validation specifics for M.Sc. Data Science live in `docs/data_science_master.md`;
the enumerated rule lists live in each degree's `degree_rules.py` (the code is
the source of truth — do not restate the lists here).

## Degree registry

`backend/app/domain/degrees/__init__.py` maps degree ids to `DegreeDefinition`
instances (`definition.py`). Every session is bound to exactly one degree; the
LLM never chooses or infers it. Currently registered: `msc_informatik`
(M.Sc. Informatik, SPO 2014), `msc_data_science` (M.Sc. Data Science,
FU-Mitteilungen 18/2021), and `bsc_informatik` (B.Sc. Informatik,
FU-Mitteilungen 23/2023). The B.Sc. package provides its 2023 programme-rules
catalogue and the locally supplied SoSe 2026 offering projection. Its
deterministic study-plan validation remains unavailable. The B.Sc. projection
does not imply that modules are offered in other semesters; its 0084d maths
entries are free-elective candidates only and still require recognition and
relevance confirmation.

Each degree package owns:

```text
prompts.py         -> all LLM prompt text + study-plan parse schema
degree_rules.py    -> deterministic validate_study_plan()
program_rules.py   -> structured display catalogue (shared models from app.domain.program_rules)
module_catalog.py  -> canonical module list (checklist-style degrees only)
__init__.py        -> assembles the DegreeDefinition
```

`DegreeDefinition` fields beyond prompts/rules: `study_plan_schema` (parser LLM
output schema), `enrich_study_plan` (deterministic post-parse enrichment),
`course_areas` (area vocabulary for course-offering placements), and
`course_modules` (canonical id -> display name map).

Validation styles differ by degree and should stay per-degree functions behind
the common interface, not a generic rule engine:

- `msc_informatik`: LP arithmetic over areas plus flags (specialization
  minimums, Wahlbereich caveats, ungraded/Bachelor caps).
- `msc_data_science`: checklist matching against the canonical module list; the
  profile (Life Sciences vs Technologies) is inferred from its mandatory marker
  modules, never declared by the LLM.

**Adding a degree:** create the package, register it in `_DEGREES`, and add
focused validator tests. Nothing else needs to change; the API, frontend picker,
and course-offering validation pick it up from the registry.

## Course-offering data

The catalogue has three layers:

```text
backend/app/domain/data/courses.json                     # shared course identity/name/LP/aliases
backend/app/domain/data/degree_modules/<degree>.json     # degree credit mappings and validation flags
backend/app/domain/data/course_offerings/<semester>.json # type, schedule, description, URL
```

Each course has one global ID, even if it appears in only one known semester.
Degree mappings state how that course is creditable for a particular regulation;
an offering file records only its semester-specific delivery details:

```json
{
  "course_id": "telematik",
  "type": "vl",
  "lp": 10,
  "schedule": null,
  "description": null,
  "url": null
}
```

Cross-file invariants, enforced at load time by
`app.domain.course_offerings.validate_course_catalog` (and guarded by
`tests/test_course_offerings.py::test_real_data_file_is_valid`):

- IDs must resolve across all three layers.
- Credit mappings must use a known degree module and one of that degree's areas.
- A course may map to multiple modules/areas within one degree.
- Offering-level LP remains a semester-specific override when the delivery
  differs from the canonical module LP.
- Bachelor-module markers remain part of degree credit mappings so the lookup
  context renders the 15 LP cap caveat.

`project_offerings(degree_id)` builds the per-degree
`semester -> area -> course_type` bucket tree deterministically; the LLM
course-key selector only ever sees the tree for the session's degree.
`tests/fixtures/msc_informatik_buckets_pre_migration.json` pins the projected
Master tree to the pre-migration bucket file.

## Program rules catalogue

Structured display rules live per degree:

```text
backend/app/domain/program_rules.py                  # shared models + render_rules_context()
backend/app/domain/degrees/<degree>/program_rules.py # per-degree catalogue content
```

Purpose:

- Source for the frontend Degree Rules tab (selected via `?degree=`).
- Human-readable catalogue of degree-rule sections, items, sources, and related
  validation issue codes.
- Stable JSON projection through `GET /api/program-rules`.

The frontend calls the API and renders structured JSON; it must not own or
duplicate degree-rule validation.

### Ownership split

```text
degrees/<d>/degree_rules.py       -> executable validation logic
degrees/<d>/program_rules.py      -> structured human-readable rule catalogue
degrees/<d>/prompts.py            -> RULES_CONTEXT rendered from that degree's catalogue
data/courses.json                 -> shared canonical course facts
data/degree_modules/<d>.json      -> degree-specific credit mappings and validation metadata
data/course_offerings/<term>.json -> semester-specific delivery data
frontend/services/api             -> API client only, no validation-rule ownership
```

When rule behavior changes, update in the affected degree package, in order:

1. `degree_rules.py`
2. `program_rules.py`
3. focused tests (`test_rule_checker.py` for msc_informatik,
   `test_data_science_rules.py` for msc_data_science)

The Softwareprojekt and Wissenschaftliches Arbeiten Wahlbereich caveats must
stay visible in both validation and display rules. For msc_informatik,
`is_wahlbereich` is separate from `area`: a module can have area `technical`
while still being counted in Wahlbereich for the seminar/project maximum caveat.

## Study-plan validation principle

```text
LLM parses -> Python validates -> LLM explains
```

The LLM may parse and explain, but must not be trusted for final LP validation.
Shared deterministic code:

```text
backend/app/domain/study_plan.py    # shared StudyPlan/PlannedModule models
backend/app/domain/rule_check.py    # shared RuleIssue/RuleCheckResult
backend/app/domain/module_catalog.py # Master enrichment + shared normalize_module_name
```

See `docs/study-plan-data.md` for the schemas and data flow.
