# Agent Flow

This document describes the LangGraph flow used by the FU Berlin CS consultant.

The graph is defined in:

```text
backend/app/services/agent_graph_service.py
```

The shared graph state is defined in:

```text
backend/app/services/states/consultant_state.py
```

Agent-flow tuning defaults are defined in:

```text
backend/app/services/agent_config.py
```

## High-Level Flow

```text
START
  -> ScopeClassifier
      -> off_topic      -> OfftopicReply -> END
      -> study_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check     -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

Degree rules reach the system prompt through `app.prompts.RULES_CONTEXT`, which
is rendered from `backend/app/domain/program_rules.py`; the `plan_check` path
skips retrieval entirely. Course-offering questions on the `study_question` path
use exact lookup buckets from `backend/app/domain/data/course_offerings.json`;
Qdrant retrieval code remains in the repository but is no longer wired into the
active graph.

## State Keys

| State key | Producer | Consumer |
|---|---|---|
| `messages` | API input, `answer_composer`, `offtopic` | all LLM nodes |
| `message_type` | `scope_classifier` | graph router, downstream nodes |
| `course_lookup_keys` | `course_key_selector` | `course_lookup`, `answer_composer` |
| `course_lookup_invalid_keys` | `course_key_selector` | `course_lookup` |
| `course_lookup_needs_clarification` | `course_key_selector` | `course_lookup`, `answer_composer` |
| `course_lookup_clarification_question` | `course_key_selector` | `course_lookup`, `answer_composer` |
| `course_lookup_message` | `course_key_selector` | `course_lookup`, `answer_composer` |
| `retrieved_context` | `course_lookup` | `answer_composer` |
| `citations` | `course_lookup` | API response, `answer_composer` context |
| `parsed_study_plan` | `study_plan_parser` | `rule_checker` |
| `rule_check_result` | `rule_checker` | `answer_composer`, API response |
| `reply` | `answer_composer`, `offtopic` | API response |

`messages` uses an append reducer, so new user and assistant messages are appended to the session thread.

## Node Responsibilities

### ScopeClassifier

File:

```text
backend/app/services/nodes/scope_classifier.py
```

Purpose:

- Classify the latest user message.
- Return one of:
  - `study_question`
  - `plan_check`
  - `off_topic`

Behavior:

- Uses the active LLM provider.
- Falls back to a local heuristic if the LLM call fails.
- Does not answer the user.

### CourseKeySelector

File:

```text
backend/app/services/nodes/course_key_selector.py
```

Purpose:

- Select exact course-offering bucket keys from the local tree.
- Output keys in `semester/area/course_type` format, for example
  `sose26/technical/swp`.
- Output multiple keys for broad questions, for example all SWP buckets in a
  semester when no area is specified.
- Ask for clarification when the user asks about course offerings but omits the
  semester.
- Output no keys for pure degree-rule questions that do not need course
  offerings.

Behavior:

- Uses the active LLM provider.
- Falls back to a local heuristic if the LLM call fails.
- Does not output course-specific slugs or title filters; title matching is left
  to the final answer over the returned buckets.
- Receives a configurable recent conversation window
  (`AGENT_COURSE_SELECTOR_HISTORY_TURNS`, default `2`).
- The prompt includes a semester coverage note derived from
  `course_offerings.json`, for example that only `sose26` is currently present.

### CourseLookup

File:

```text
backend/app/services/nodes/course_lookup.py
```

Purpose:

- Validate selector keys against `course_offerings.json`.
- Return the whole selected buckets as deterministic `retrieved_context`.
- Add bucket-level citations and course URL citations where URLs exist.
- Preserve Qdrant-free behavior for normal study questions.

Output:

```text
retrieved_context
citations
```

Course lookup runs only on the `study_question` path. Degree rules are rendered
from `program_rules.py` into `app.prompts.RULES_CONTEXT`. Plan checks rely on
the deterministic Python validator plus rules in the system prompt, so they do
not hit Qdrant.

### Legacy Retrieval

The old Qdrant retrieval node still exists in:

```text
backend/app/services/nodes/retrieval.py
```

It is kept for possible future RAG experiments and manual ingestion workflows,
but it is not connected to the compiled graph.

### StudyPlanParser

File:

```text
backend/app/services/nodes/study_plan_parser.py
```

Purpose:

- Extract a structured `StudyPlan` from the user's message.

Behavior:

- Uses the active LLM provider with a structured JSON schema.
- Falls back to a heuristic parser if the LLM call fails.
- Enriches parsed modules through `module_catalog.py`.

Important:

- The parser is not trusted for final validity.
- It only creates structured input for the deterministic rule checker.

### RuleChecker

File:

```text
backend/app/services/nodes/rule_checker.py
```

Purpose:

- Run deterministic validation on `parsed_study_plan`.

Implementation:

```text
backend/app/domain/degree_rules.py
```

Output:

```text
rule_check_result
```

This node owns the actual pass/fail decision for LP totals, specialization requirements, seminar/project counts, Wahlbereich caveats, ungraded LP, Bachelor-module LP, and duplicate modules.

### AnswerComposer

File:

```text
backend/app/services/nodes/answer_composer.py
```

Purpose:

- Produce the final assistant response.

Inputs:

- Latest user message
- Configurable recent conversation window
  (`AGENT_ANSWER_COMPOSER_HISTORY_TURNS`, default `4`)
- Retrieved context from exact course-offering lookup, when applicable
- Optional deterministic rule-check result

Rules:

- Answer in the same language as the user.
- Use only retrieved context and deterministic validation results.
- Do not invent Studienordnung or Pruefungsordnung rules.
- State uncertainty when the local resources do not answer the question.
- Keep the answer advisory.

### Offtopic

File:

```text
backend/app/services/nodes/offtopic.py
```

Purpose:

- Return a short redirect for messages unrelated to the FU Berlin Master Informatik.

Behavior:

- Uses a simple German/English heuristic.
- Does not call the LLM.

## Routing Logic

`route_after_classifier()` lives in:

```text
backend/app/services/routing.py
```

It maps:

```text
plan_check     -> study_plan_parser
study_question -> course_key_selector (then course_lookup, then answer_composer)
everything else -> offtopic
```

## Error Handling Strategy

LLM-dependent nodes use local fallbacks where possible:

- `ScopeClassifier`: heuristic classifier
- `CourseKeySelector`: heuristic selector
- `StudyPlanParser`: heuristic module/LP parser
- `AnswerComposer`: compact fallback answer

Course lookup failures return an empty context, empty citations, or a concise
clarification/missing-data note.

This keeps the API responsive even when the LLM fails. Qdrant availability no
longer affects the active study-question flow.

## HTML Overview

A visual graph is available in:

```text
docs/agent-flow.html
```
