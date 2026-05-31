# Study Plan Data

This document describes how the FU Berlin CS consultant currently represents, stores, and validates a student's study-program data.

## Current Storage Model

Phase 1 does not persist study-plan data to disk or a database.

The backend uses LangGraph `MemorySaver` in `backend/app/services/agent_graph_service.py`. A session is identified by `session_id`, and that ID is passed to LangGraph as:

```python
config = {"configurable": {"thread_id": session_id}}
```

The graph state for that thread holds:

```text
messages
message_type
retrieval_query
course_lookup_keys
course_lookup_needs_clarification
retrieved_context
citations
parsed_study_plan
rule_check_result
reply
```

Important implications:

- The study plan is in memory only.
- The study plan is lost when the backend process restarts.
- The current design is not multi-instance safe.
- There is no audit trail.
- There is no dedicated endpoint yet for reading or editing a study plan.
- A parsed plan exists only after a message has gone through the `plan_check` path.

## Data Flow

```text
POST /api/sessions
  -> SessionService.create_session()
  -> returns session_id

POST /api/sessions/{session_id}/message
  -> SessionService.process_message()
  -> LangGraph ainvoke(..., thread_id=session_id)
  -> agent graph updates in-memory ConsultantState
```

For a normal study question, the graph may store exact course-offering lookup
context and citations, but no study plan.

For a plan-check message, the graph stores:

```text
parsed_study_plan
rule_check_result
```

The API response includes `rule_check_result` when available.

## StudyPlan Schema

The canonical in-process schema lives in `backend/app/domain/study_plan.py`.

```python
class StudyPlan(BaseModel):
    specialization_area: Literal["practical", "theoretical", "technical"] | None
    modules: list[PlannedModule]
```

The specialization area is the chosen Vertiefung:

- `practical`
- `theoretical`
- `technical`
- `None` when not supplied or not parseable

## PlannedModule Schema

```python
class PlannedModule(BaseModel):
    name: str
    lp: int
    area: Literal[
        "practical",
        "theoretical",
        "technical",
        "application",
        "thesis",
        "unknown",
    ]
    is_wahlbereich: bool
    is_ungraded: bool
    is_bachelor_module: bool
    is_scientific_work: bool
    is_software_project: bool
```

Field meaning:

| Field | Meaning |
|---|---|
| `name` | Module name as parsed from the user or normalized from the catalog. |
| `lp` | Leistungspunkte. Missing LP defaults to `0` and becomes a validation error. |
| `area` | Subject area used for LP totals and specialization checks. |
| `is_wahlbereich` | Whether the module is explicitly counted in Wahlbereich. |
| `is_ungraded` | Whether the module is ungraded or non-differentiated. |
| `is_bachelor_module` | Whether the module counts toward the Bachelor-module cap. |
| `is_scientific_work` | Whether it is a Wissenschaftliches Arbeiten module. |
| `is_software_project` | Whether it is a Softwareprojekt module. |

## User Data vs Inferred Data

The study plan parser extracts what the user says. Then `module_catalog.py` enriches modules using `module_catalog.json`.

User-provided data can include:

- module name
- LP
- area
- specialization area
- whether a module is in Wahlbereich
- whether a module is ungraded
- whether a module is a Bachelor module

Catalog-inferred data can include:

- canonical module name
- LP
- area
- ungraded marker
- Bachelor-module marker
- Wissenschaftliches Arbeiten marker
- Softwareprojekt marker

The implementation intentionally keeps the LLM out of final validation. The LLM may parse a plan, but `degree_rules.py` decides whether the plan passes.

## Wahlbereich Handling

`is_wahlbereich` is separate from `area`.

This matters because a module can still belong to a subject area, for example `technical`, while being counted in Wahlbereich for the seminar/project maximum caveat.

Current behavior:

- Wahlbereich LP is reported as `wahlbereich_lp`.
- Wahlbereich LP must not exceed 10 LP.
- Core Softwareprojekt count excludes modules with `is_wahlbereich=true`.
- Total Softwareprojekt count includes them.
- Core Wissenschaftliches Arbeiten count excludes modules with `is_wahlbereich=true`.
- Total Wissenschaftliches Arbeiten count includes them.

This implements the caveat:

- Core Softwareprojekt modules: at least 1 and at most 2.
- One extra Softwareprojekt can be placed in Wahlbereich, allowing 3 total.
- Core Wissenschaftliches Arbeiten modules: at least 2 and at most 4.
- Up to 2 extra Wissenschaftliches Arbeiten modules can be placed in Wahlbereich, because seminars are 5 LP and Wahlbereich is 10 LP.

## RuleCheckResult Schema

Validation output is produced by `backend/app/domain/degree_rules.py`.

```python
class RuleCheckResult(BaseModel):
    is_valid: bool
    summary: str
    totals: dict[str, int]
    issues: list[RuleIssue]
```

The `totals` dict currently includes:

```text
practical_lp
theoretical_lp
technical_lp
application_lp
informatics_lp
module_area_lp
thesis_lp
master_total_lp
ungraded_lp
bachelor_module_lp
wahlbereich_lp
core_scientific_work_count
total_scientific_work_count
core_software_project_count
total_software_project_count
```

Each issue has:

```python
class RuleIssue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str
    details: dict[str, Any]
```

## Current Limitations

- No persistent student profile exists.
- No explicit `GET /api/sessions/{id}/study-plan` endpoint exists.
- No explicit `PUT /api/sessions/{id}/study-plan` endpoint exists.
- The study plan is currently extracted from chat text, not edited through a structured API.
- The parser may miss modules when the user writes an ambiguous or incomplete plan.
- Unknown modules can still be included, but they need explicit LP and area data or they produce validation issues/warnings.

## Recommended Phase 2 Persistence

The next clean step is to make the study plan an explicit resource:

```text
GET  /api/sessions/{id}/study-plan
PUT  /api/sessions/{id}/study-plan
POST /api/sessions/{id}/study-plan/check
```

For quick local development, store JSON files:

```text
backend/data/sessions/{session_id}.json
```

Suggested shape:

```json
{
  "session_id": "uuid",
  "created_at": "iso-8601",
  "updated_at": "iso-8601",
  "study_plan": {
    "specialization_area": "practical",
    "modules": []
  },
  "last_rule_check_result": null
}
```

For real deployment, move the same schema to SQLite or Postgres. The API contract should stay the same so the storage backend can change later.
