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
      -> off_topic                -> OfftopicReply -> END
      -> degree_question          -> AnswerComposer -> END
      -> course_offering_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check               -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

Degree rules reach the system prompt through `app.prompts.RULES_CONTEXT`, which
is rendered from `backend/app/domain/program_rules.py`; the `plan_check` path
skips retrieval entirely. Pure degree-rule questions on the `degree_question`
path also skip course lookup and go straight to `AnswerComposer`.
Course-offering questions on the `course_offering_question` path use exact
lookup buckets from `backend/app/domain/data/course_offerings.json`. The legacy
Qdrant retrieval and query-rewriter nodes have been removed from the runtime.

## State Keys

| State key | Producer | Consumer |
|---|---|---|
| `messages` | API input, `answer_composer`, `offtopic` | all LLM nodes |
| `wizardflow_message_id` | `SessionService` | every active node, WizardFlow finalization |
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
  - `degree_question`
  - `course_offering_question`
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

Course lookup runs only on the `course_offering_question` path. Degree rules
are rendered from `program_rules.py` into `app.prompts.RULES_CONTEXT`; pure
degree questions go directly from `ScopeClassifier` to `AnswerComposer`. Plan
checks rely on the deterministic Python validator plus rules in the system
prompt, so they do not hit Qdrant.

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
plan_check               -> study_plan_parser
degree_question          -> answer_composer
course_offering_question -> course_key_selector (then course_lookup, then answer_composer)
everything else          -> offtopic
```

## WizardFlow Tracing

`SessionService` creates a new UUID for each chat request or transcript upload
and stores it in `ConsultantState.wizardflow_message_id`. The same UUID is passed
to each node and finalized once at the request boundary.

The compiled graph topology is registered through
`wizardflow.init_from_langgraph`. All active nodes log explicitly:

- LLM nodes: `llm_input`, `llm_output`, `llm_error`, and `node_output`.
- Deterministic nodes: `node_input` and `node_output`.

Each `llm_input` contains both the exact system `prompt` and provider `msg`.
Transcript parser messages are intentionally unredacted. Generated JSONL files
are written to `backend/traces/` by default and excluded from Git.

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
