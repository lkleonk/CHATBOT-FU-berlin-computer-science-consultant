# DO NOT USE GIT

# FU Berlin CS Consultant Implementation Plan

Phase 1 goal: backend-only LLM consultant for FU Berlin Informatik Master questions, using the existing files in `ressources/` as source material. The implementation must stay fully inside `fu_berlin_cs_consultant/`.

## Scope

[x] Only create/edit files under `fu_berlin_cs_consultant/`.
[x] Keep existing `fu_berlin_cs_consultant/ressources/` path as-is.
[x] Do not import from the root `backend/`; copy/adapt patterns locally where needed.
[x] Do not change any code outside `fu_berlin_cs_consultant/`.
[x] Do not build a frontend in phase 1.

## Backend Skeleton

[x] Create `fu_berlin_cs_consultant/backend/`.
[x] Add `backend/app/main.py` with FastAPI app, CORS, and lifespan startup.
[x] Add `backend/app/routes.py` with only:
[x] `GET /health`
[x] `POST /api/sessions`
[x] `DELETE /api/sessions/{session_id}`
[x] `POST /api/sessions/{session_id}/message`
[x] Add `backend/app/models.py` for Pydantic request/response contracts.
[x] Add `backend/app/settings.py` for env-based config.

## Docker

[x] Add `fu_berlin_cs_consultant/docker-compose.yml`.
[x] Add backend service.
[x] Add optional Qdrant service behind the `legacy-rag` Compose profile.
[x] Do not add frontend service.
[x] Do not add Postgres initially; use in-memory LangGraph/session state for phase 1.
[x] Add `backend/Dockerfile`.
[x] Add `backend/requirements.txt`.
[x] Keep Torch, SentenceTransformer, and Qdrant in optional `backend/requirements-legacy-rag.txt` only.
[x] Add `.env.example`.

## LLM Providers

[x] Add `services/model_service.py` provider selector.
[x] Add `services/academiccloud_service.py`.
[x] Add `services/ollama_service.py`.
[x] Add `services/ssh_manager.py` for FU Ollama tunnel support.
[x] Support `LLM_PROVIDER=academiccloud` / `fu_ollama` / `local_ollama`.
[x] Support `ACADEMICCLOUD_BASE_URL`, `ACADEMICCLOUD_API_KEY`, `ACADEMICCLOUD_MODEL`.
[x] Support `LOCAL_OLLAMA_HOST`, `LOCAL_OLLAMA_MODEL`.
[x] Support `FU_OLLAMA_MODEL` and auto SSH tunnel via `FU_SSH_HOST`, `FU_SSH_PORT`, `FU_SSH_USER`, `FU_SSH_PASSWORD`, `FU_REMOTE_BIND_ADDRESS`, `FU_REMOTE_BIND_PORT`.
[x] Add `/health` checks for the active LLM provider. Qdrant is reported as disabled legacy/manual RAG.

## RAG Ingestion, Manual Only

[x] Add `backend/scripts/extract_pdf.py`.
[x] Add `backend/scripts/ingest_resources.py`.
[x] Ingest from `fu_berlin_cs_consultant/ressources/`.
[x] Support `.txt`.
[x] Support `.pdf` via `pypdf`.
[x] Normalize extracted text.
[x] Chunk by semantic sections where possible.
[x] Store source metadata:
[x] filename
[x] document title
[x] chunk id
[x] page number if PDF
[x] section heading if available
[x] content hash
[x] Use a dedicated Qdrant collection, e.g. `fu_cs_consultant_knowledge`.
[x] Use multilingual embeddings for German/English queries.
[x] Make ingestion rebuild the collection deterministically.
[x] Do not add a `POST /api/ingest` route.

Manual ingestion command target:

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest
```

## Knowledge Artifacts

[x] Add `backend/knowledge_base/generated/`.
[x] Generate or hand-curate `degree_rules.md` from `Informatik_Master_Ablauf.txt`.
[x] Generate or hand-curate `module_catalog.md` from the checklist PDF.
[x] Generate `module_catalog.json` for deterministic module lookup.
[x] Keep original source files untouched in `ressources/`.

## Domain Logic

[x] Add `backend/app/domain/degree_rules.py`.
[x] Add `backend/app/domain/module_catalog.py`.
[x] Add `backend/app/domain/study_plan.py`.
[x] Encode deterministic rules:
[x] Master total: 120 LP including thesis.
[x] Module area before thesis: 90 LP.
[x] Master thesis: 30 LP.
[x] Informatik area: 70-80 LP.
[x] Anwendungsbereich: 10-20 LP.
[x] Practical Informatics minimum 20 LP, or 40 LP if specialization.
[x] Technical Informatics minimum 10 LP, or 30 LP if specialization.
[x] Theoretical Informatics minimum 10 LP, or 30 LP if specialization.
[x] Exactly one specialization area.
[x] Scientific work modules: at least 2, at most 4.
[x] At least one scientific work module in the specialization area.
[x] Software projects: at least 1, at most 2.
[x] Ungraded modules: 25-30 LP.
[x] Bachelor modules: max 15 LP.
[x] Same exact module cannot count twice.
[x] Return structured validation results: pass/fail/warning, missing LP, excess LP, explanation.

## Agent State

[x] Add `services/states/consultant_state.py`.
[x] Track:
[x] messages
[x] wizardflow_message_id
[x] message_type
[x] course_lookup_keys
[x] course_lookup_needs_clarification
[x] retrieved_context
[x] parsed_study_plan
[x] rule_check_result
[x] reply
[x] citations

## Agent Nodes

[x] Add `nodes/scope_classifier.py`.
[x] Add `nodes/course_key_selector.py`.
[x] Add `nodes/course_lookup.py`.
[x] Add `nodes/study_plan_parser.py`.
[x] Add `nodes/rule_checker.py`.
[x] Add `nodes/answer_composer.py`.
[x] Add `nodes/offtopic.py`.

## Agent Flow

[x] Add `services/agent_graph_service.py`.

Target flow:

```text
START
  -> ScopeClassifier
      -> off_topic                -> OfftopicReply -> END
      -> degree_question          -> AnswerComposer -> END
      -> course_offering_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check               -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

The legacy Qdrant retrieval and query-rewriter nodes have been removed. Current
course offerings are read from
`backend/app/domain/data/course_offerings.json` with keys such as
`sose26/technical/swp`.

## WizardFlow Tracing

[x] Add `wizardflow==0.3.0`.
[x] Initialize tracing from the compiled LangGraph topology; keep the client
    as the module global `tracer` in `services/wizardflow_service.py`.
[x] Rotate to a fresh trace file on demand via `POST /api/tracing/reinit`
    (`tracer.reinit()`), triggered by the `New Trace File` button in the
    Settings developer section.
[x] Generate one UUID per chat message or transcript upload.
[x] Store `wizardflow_message_id` in `ConsultantState`.
[x] Log `llm_input` with `prompt` and unredacted `msg`.
[x] Log `llm_output`, fallback errors, and deterministic node input/output.
[x] Do not log `__start__`; keep `__end__` payload-free.
[x] Persist Docker traces under `backend/traces/` and exclude them from Git.

## Prompt Design

[x] Add `app/prompts.py`.
[x] Define consultant identity: FU Berlin Informatik Master study consultant.
[x] Require grounded answers from retrieved context.
[x] Require uncertainty when resources do not answer.
[x] Support German and English.
[x] For plan checks, force structured JSON extraction before deterministic validation.
[x] Do not let the LLM invent Studienordnung or Pruefungsordnung rules.

## Session Service

[x] Add `services/session_service.py`.
[x] Create UUID session IDs.
[x] Use LangGraph `thread_id=session_id`.
[x] Expire inactive in-memory sessions opportunistically and delete reset sessions explicitly.
[x] Return one assistant reply per user message.
[x] Include citations in response where available.
[x] Include structured rule-check result when applicable.

## Usage And Frontend Safety UX

[x] Expose read-only client usage through `GET /api/usage`.
[x] Return scoped rate-limit headers for chat and transcript actions.
[x] Show a persistent clickable request-allowance chip.
[x] Warn once per reset period at ten or fewer remaining requests.
[x] Add a versioned welcome dialog with unofficial-service, quota, retention,
    transcript-processing, and tracing disclosures.
[x] Export the locally stored chat as Markdown.
[x] Keep `Reset conversation` visible in production with confirmation and a
    download option.
[x] Hide API/session diagnostics, health details, and dummy data behind
    `NEXT_PUBLIC_ENABLE_DEV_TOOLS`.
[x] Set the default inactivity retention to 48 hours.

## Tests

[x] Add `backend/tests/test_rule_checker.py`.
[x] Test valid plan.
[x] Test missing specialization LP.
[x] Test too many ungraded LP.
[x] Test too many Bachelor-module LP.
[x] Test too few scientific work modules.
[x] Test too many software projects.
[x] Add `backend/tests/test_resource_ingestion.py`.
[x] Add `backend/tests/test_agent_routes.py` for routing labels.

## Docs

[x] Add `fu_berlin_cs_consultant/README.md`.
[x] Document Docker startup.
[x] Document manual ingestion.
[x] Document env vars for AcademicCloud and FU Ollama.
[x] Document API examples.
[x] State clearly that this is advisory and should reference official FU rules.

## Verification

[ ] Build Docker image.
[ ] Start backend + frontend.
[ ] Optional: start Qdrant with `docker compose --profile legacy-rag up -d qdrant`.
[ ] Run manual ingestion.
[ ] Confirm `/health`.
[ ] Ask a simple course-offering lookup question.
[ ] Ask a study-plan validation question.
[x] Run tests.
[x] Run the full backend suite from runtime-only requirements without legacy RAG dependencies.
[x] Confirm no files outside `fu_berlin_cs_consultant/` changed.

## Multi-Degree Support

Phase 1 — degree framework:

[x] Add `domain/degrees/definition.py` (`DegreeDefinition` + `DegreePrompts`).
[x] Add `domain/degrees/__init__.py` registry with `DEFAULT_DEGREE_ID=msc_informatik`.
[x] Move Master Informatik prompts/rules/catalogue into `domain/degrees/msc_informatik/`; remove `app/prompts.py`.
[x] Extract shared `RuleIssue`/`RuleCheckResult` into `domain/rule_check.py`.
[x] Seed `degree_id` into the LangGraph checkpoint at session creation; nodes resolve prompts via `degree_for(state)`.
[x] `POST /api/sessions` accepts `{"degree": ...}`; add `GET /api/degrees`; `GET /api/program-rules?degree=`.

Phase 2 — shared course offerings:

[x] Convert `course_offerings.json` to a flat tagged list (placement lists per degree, `lp` override, `module_id(s)`, `is_bachelor_module`).
[x] Deterministic per-degree projection to `semester/area/type` bucket trees; selector/lookup nodes are degree-scoped.
[x] Load-time validation against the registry (area vocabulary, canonical module ids).
[x] Migration-equivalence test against the pre-migration Master buckets fixture.
[x] `CourseKeySelector` short-circuits without an LLM call for degrees without tagged offerings.

Phase 3 — degree packages:

[x] `msc_data_science`: canonical module catalogue, profile-inference checklist validator, rules catalogue, prompts, tests.
[ ] `bsc_informatik`: blocked on the §7(3) Pflicht and §7(4) Wahlpflicht module lists (SPO 2023).
[ ] Tag Data Science entries in `course_offerings.json` once the curated offerings data is ready.

Phase 4 — frontend:

[x] `DegreeContext` (fetches `/api/degrees`, persists choice in localStorage).
[x] Welcome dialog collects the degree with card-style toggle buttons.
[x] Header degree switcher with `DegreeSwitchDialog` (data-loss warning, chat download, Study Plan print shortcut).
[x] Session creation sends the degree; Degree Rules tab refetches per degree.

Phase 5 — docs:

[x] Update `AGENTS.md`, `README.md`, `docs/agent-flow.md`, `docs/agent-flow.html`, `docs/frontend.md`, `implementation.md`.
