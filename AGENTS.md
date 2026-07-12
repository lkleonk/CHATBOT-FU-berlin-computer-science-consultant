# AGENTS.md

Instructions for agents working in `fu_berlin_cs_consultant/`.

## Hard Rules

- Do not use Git, except for read-only operations like `git diff`, `git status`, `git log`, and `git show`.
- Do not edit files outside `fu_berlin_cs_consultant/`.
- Do not add a public ingestion endpoint.
- Keep original files under `ressources/` untouched unless the user explicitly asks to update source material.
- Frontend work is allowed only inside `fu_berlin_cs_consultant/frontend/`.

## Project Purpose

Public website: `https://cs-modulio.com`

This is a FU Berlin study consultant for multiple degree programs with a backend-first architecture and a standalone Next.js frontend. Supported degrees live in a registry (`backend/app/domain/degrees/`): currently `msc_informatik` (M.Sc. Informatik, SPO 2014) and `msc_data_science` (M.Sc. Data Science, FU-Mitteilungen 18/2021). A `bsc_informatik` package is planned once its §7(3)/(4) module lists are available.

It answers questions using exact local course-offering lookup plus rules in prompts, while preserving optional local RAG code for future/manual retrieval experiments. It validates proposed study plans with deterministic per-degree Python rules. The LLM may parse and explain, but the LLM must not be trusted for final LP validation. Every session is bound to exactly one degree; the LLM never chooses or infers the degree.

## Important Paths

```text
fu_berlin_cs_consultant/
  README.md
  implementation.md
  docker-compose.yml
  .env.example
  ressources/
  docs/
  backend/
    app/
      main.py
      routes.py
      models.py
      settings.py
      domain/
        course_offerings.py
        program_rules.py        # generic catalogue models + prompt renderer
        rule_check.py           # shared RuleIssue/RuleCheckResult
        study_plan.py
        module_catalog.py
        data/course_offerings.json
        degrees/
          __init__.py           # registry: list_degrees(), get_degree(), DEFAULT_DEGREE_ID
          definition.py         # DegreeDefinition + DegreePrompts contract
          msc_informatik/       # prompts.py, degree_rules.py, program_rules.py
          msc_data_science/     # + module_catalog.py (canonical checklist modules)
      services/
      pdf/
    scripts/
    knowledge_base/generated/
    tests/
  frontend/
    Dockerfile
    src/
      app/
      components/
      context/                  # SettingsContext, UsageContext, DegreeContext
      services/
      theme/
      types/
```

There is no `backend/app/prompts.py` anymore. Prompts are per-degree modules
(`domain/degrees/<degree>/prompts.py`) exposed through `DegreeDefinition.prompts`;
nodes resolve them via `degree_for(state)` in `services/nodes/utils.py`.

Technical docs:

```text
docs/study-plan-data.md
docs/agent-flow.md
docs/rag-ingestion.md
docs/agent-flow.html
```

## Local CLI Notes

Agents usually run in Windows PowerShell from the repository root:

```text
C:\Users\Leon Koch\Desktop\code_Freizeit\fullstack_w_llm\fu_berlin_cs_consultant
```

Prefer PowerShell-native commands for local inspection (`Get-ChildItem`,
`Get-Content`, `Select-String`) and use `rg` / `rg --files` for fast search when
available. Quote absolute paths because the user profile path contains a space
(`Leon Koch`). Run Docker Compose commands from the repository root, backend
Python/test commands from `backend/` when the command says so, and frontend
commands from `frontend/`.

## Backend API

Current public API:

```text
GET  /health
GET  /api/degrees
GET  /api/program-rules?degree=<degree_id>
GET  /api/usage
POST /api/tracing/reinit                # dev: rotate the WizardFlow trace file
POST /api/sessions                      # optional body {"degree": "<degree_id>"}
DELETE /api/sessions/{session_id}
POST /api/sessions/{session_id}/message
POST /api/sessions/{session_id}/transcript
```

No `POST /api/ingest` route should exist.

`POST /api/sessions` accepts an optional JSON body with a `degree` id
(default `msc_informatik`); unknown ids return HTTP 422 with
`detail.error_code == "unknown_degree"`. The degree id is seeded into the
LangGraph checkpoint at creation and returned in the response. All graph nodes
and transcript uploads read the session's degree from that state.

`GET /api/degrees` lists registered degrees (id, display name, regulation) for
the frontend picker. It must not consume quota or invoke the LLM.

`POST /api/sessions/{session_id}/transcript` accepts a multipart PDF upload
(field name `file`). See the "PDF Transcript Upload" section.

`GET /api/program-rules` returns the structured display catalogue for the frontend Degree Rules tab, selected by the `degree` query parameter (default `msc_informatik`). It should not require Qdrant, embeddings, LangGraph, or an LLM to answer.

`GET /api/usage` returns the current client-IP user-action allowance, UTC reset
time, configured session inactivity TTL, and whether diagnostic WizardFlow
tracing is enabled. It must not consume quota or invoke the LLM.

`POST /api/tracing/reinit` rotates the process-wide WizardFlow tracer to a
fresh timestamped trace file via `tracer.reinit()` (graph and output
configuration are kept; open messages carry over). It returns the new trace
path, or HTTP 409 with `detail.error_code == "tracing_disabled"` when tracing
is off. It is triggered manually from the frontend Settings developer section
and must not consume quota or invoke the LLM. The WizardFlow client is stored
as the module global `tracer` in `services/wizardflow_service.py`.

## Docker

`docker-compose.yml` starts the backend locally. The optional static-frontend
preview uses the `frontend-preview` profile:

```text
frontend preview -> http://localhost:3000/
backend          -> http://localhost:8000
```

The optional `production` profile also starts Caddy on ports 80/443. Caddy
terminates HTTPS, serves `frontend/out` directly from `/srv`, and proxies only
backend traffic over the internal Compose network. Production therefore runs
no Node.js frontend container. Its certificate state persists in the
`caddy_data` volume.

Qdrant is behind the optional `legacy-rag` Compose profile. Normal
`docker compose up` should not start Qdrant. Use
`docker compose --profile legacy-rag up -d qdrant` only for manual legacy RAG
ingestion or retrieval experiments.

The normal backend image installs `backend/requirements.txt`, which excludes
Torch, SentenceTransformer, and Qdrant. The optional ingestion image target
installs `backend/requirements-legacy-rag.txt`.

Compose uses `.env` as the backend env file. Keep `.env.example` aligned when adding required runtime variables.

The frontend is a static Next.js export (`output: "export"`). Build it on the
local machine with `npm run build`; the generated `frontend/out/` directory is
a tracked deployment artifact and must be refreshed before deployment. The
browser-facing API base URL is baked into that export; the optional Docker
preview image packages the export unchanged:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_DEV_TOOLS=false
```

This value is intentionally host-facing because the JavaScript runs in the user's browser, not inside the Docker network.

Compose publishes application ports on `COMPOSE_BIND_ADDRESS` and reads
`FRONTEND_PORT` (preview only), `CONSULTANT_PORT`, `CORS_ALLOWED_ORIGINS`, and
`FORWARDED_ALLOW_IPS` from `.env`. Keep the application bind address on loopback
when the production Caddy profile is enabled. Production additionally requires
`APP_DOMAIN`, a static export built with the matching `NEXT_PUBLIC_API_BASE_URL`,
and matching CORS configuration.

## Agent Flow

Implemented in `backend/app/services/agent_graph_service.py`.

```text
START
  -> ScopeClassifier
      -> off_topic                -> OfftopicReply -> END
      -> degree_question          -> AnswerComposer -> END
      -> course_offering_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check               -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

Every node is degree-scoped: it resolves the session's `degree_id` from graph
state (`degree_for(state)` in `services/nodes/utils.py`, falling back to
`DEFAULT_DEGREE_ID`) and pulls its system prompt, parse schema, enrichment, and
validator from the `DegreeDefinition`. Degree rules reach the system prompt
through each degree's `prompts.RULES_CONTEXT`, rendered from that degree's
`program_rules.py` via the shared `render_rules_context()`. The `plan_check`
path does not need retrieval before parsing. Pure degree-rule questions on the
`degree_question` path skip course lookup and go straight to `AnswerComposer`.
Course-offering lookup on the `course_offering_question` path reads exact
buckets from the per-degree projection of
`backend/app/domain/data/course_offerings.json`, using keys like
`sose26/technical/swp`. When a degree has no tagged course-offering entries,
`CourseKeySelector` short-circuits (no LLM call) with an honest "no local
course-offering data" note. The legacy Qdrant retrieval and query-rewriter
nodes have been removed; manual ingestion and vector-service code remain
available.

`MemorySaver` is used for phase 1, so session state is in memory and lost on
backend restart. Sessions also expire after 48 hours of inactivity through
opportunistic cleanup. `DELETE /api/sessions/{session_id}` removes inactive
state immediately or defers deletion until an active request finishes.

Session lifecycle env knobs:

```text
SESSION_INACTIVITY_TTL_SECONDS
SESSION_CLEANUP_INTERVAL_SECONDS
```

## Usage Quotas

Deployment quotas are process-local Python state in
`backend/app/services/quota_service.py`. They reset at 00:00 UTC and whenever
the backend process restarts. Run one backend worker if the configured values
must remain the effective global limits.

Default limits:

```text
DAILY_LLM_INVOCATIONS=200
DAILY_USER_ACTIONS=100
```

Every call through `ModelService.chat()` or `ModelService.invoke()` consumes
one global LLM invocation. A single chat action can therefore consume multiple
LLM invocations. The user-action limit applies per client IP to chat messages
and transcript uploads. Creating or deleting sessions, reading program rules,
and checking health do not consume user actions. Quota exhaustion returns HTTP
429 with a structured error payload and rate-limit headers. Successful user
actions expose user-action rate-limit headers; global LLM headers use a
different scope and must not be rendered as a user's allowance. There is no LLM
concurrency cap.

Agent-flow tuning lives in `backend/app/services/agent_config.py`. Current env
knobs include:

```text
AGENT_COURSE_SELECTOR_HISTORY_TURNS
AGENT_COURSE_SELECTOR_MAX_KEYS
AGENT_COURSE_SELECTOR_INCLUDE_SEMESTERS_NOTE
AGENT_ANSWER_COMPOSER_HISTORY_TURNS
```

Do not duplicate available semesters in settings. The course selector derives
semester coverage from the session degree's projection of
`backend/app/domain/data/course_offerings.json`.

## Degree Registry

`backend/app/domain/degrees/__init__.py` maps degree ids to `DegreeDefinition`
instances (`definition.py`). Each degree package owns:

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
`course_modules` (canonical id -> display name map, or `None` when the degree
has no canonical module list).

Validation styles differ by degree and should stay per-degree functions behind
the common interface, not a generic rule engine:

- `msc_informatik`: LP arithmetic over areas plus flags (specialization
  minimums, Wahlbereich caveats, ungraded/Bachelor caps).
- `msc_data_science`: checklist matching against the canonical module list;
  the profile (Life Sciences vs Technologies) is inferred from its mandatory
  marker modules, never declared by the LLM.

Adding a degree: create the package, register it in `_DEGREES`, and add focused
validator tests. Nothing else needs to change; the API, frontend picker, and
course-offering validation pick it up from the registry.

## Course Offerings Data

`backend/app/domain/data/course_offerings.json` is a flat list of offered
courses. Each course appears once per semester and carries a `degrees` map
tagging every degree it counts toward. A degree's value is a placement list
(single object allowed as shorthand) because one course can sit in multiple
areas of the same degree:

```json
{
  "semester": "sose26",
  "type": "vl",
  "title": "Telematik",
  "lp": 10,
  "schedule": null, "description": null, "url": null,
  "degrees": {
    "msc_informatik": [{ "area": "technical", "module_catalog_name": "Telematik" }],
    "msc_data_science": [{ "area": "technologies", "module_ids": ["telematik"] }]
  }
}
```

Placement rules, enforced at load time by
`app.domain.course_offerings.validate_course_entries` (and guarded by
`tests/test_course_offerings.py::test_real_data_file_is_valid`):

- `area` must be in the degree's `course_areas` vocabulary
  (`msc_informatik`: technical/practical/theoretical/application;
  `msc_data_science`: grundlagen/life_sciences/technologies).
- Degrees with `course_modules` require `module_ids` (or `module_id`
  shorthand) referencing known canonical ids; degrees without one require
  `module_catalog_name` and must not carry module ids.
- A placement may list several `module_ids` when one offering is creditable as
  multiple canonical modules (e.g. Softwareprojekt Data Science A or B).
- Placement-level `lp` overrides the entry-level default for that degree.
- `is_bachelor_module: true` marks Bachelor lectures creditable in a Master;
  the lookup context renders the 15 LP cap caveat.

`project_offerings(degree_id)` builds the per-degree
`semester -> area -> course_type` bucket tree deterministically; the LLM
course-key selector only ever sees the tree for the session's degree.
`tests/fixtures/msc_informatik_buckets_pre_migration.json` pins the projected
Master tree to the pre-migration bucket file.

## Study Plan Validation

Core deterministic code:

```text
backend/app/domain/study_plan.py                          # shared StudyPlan/PlannedModule models
backend/app/domain/rule_check.py                          # shared RuleIssue/RuleCheckResult
backend/app/domain/module_catalog.py                      # Master enrichment + shared normalize_module_name
backend/app/domain/degrees/msc_informatik/degree_rules.py
backend/app/domain/degrees/msc_data_science/degree_rules.py
backend/app/domain/degrees/msc_data_science/module_catalog.py
```

Key principle:

```text
LLM parses -> Python validates -> LLM explains
```

The `msc_data_science` validator matches parsed module names (with aliases,
via `normalize_module_name`) against its canonical catalogue, infers the
profile from mandatory marker modules, and checks Grundlagen completeness,
profile mandatory modules, the 15/15 vs 30/15 elective quotas, 90 LP module
area, 30 LP thesis, the 60 LP thesis-admission gate (warning), duplicates, and
LP mismatches (warning). Unmatched modules become a warning, not a silent
classification.

The `msc_informatik` rule checker currently handles:

- 90 LP module area before thesis
- 30 LP Masterarbeit
- 70-80 LP Informatik area
- 10-20 LP Anwendungsbereich
- specialization minimums
- Wissenschaftliches Arbeiten minimum/maximum
- Softwareprojekt minimum/maximum
- Wahlbereich caveat for extra seminars/projects
- 25-30 LP ungraded modules
- max 15 LP Bachelor modules
- duplicate module detection

`is_wahlbereich` is separate from `area`. A module can still have area `technical`, for example, while being counted in Wahlbereich for the seminar/project maximum caveat.

## PDF Transcript Upload

Users can upload a Leistungsübersicht (transcript) PDF from the Chat tab or the
Study Plan tab. There is no OCR: image-only/scanned PDFs are rejected rather than
sent to the LLM.

Pipeline (`backend/app/pdf/`):

```text
extract.py     -> PDFExtractor ABC + PyPdfExtractor (pypdf, raw per-page text)
clean.py       -> clean_pdf_text (null bytes, collapse spaces/newlines, trim only)
validation.py  -> validate_pdf_readability (per-page + total thresholds)
service.py     -> extract_and_validate (orchestrates extract -> clean -> validate)
models.py      -> ExtractedDocument, ExtractedPage, ReadabilityResult, PdfUnreadableError
```

Extraction is intentionally pluggable: a future OCR extractor subclasses
`PDFExtractor` and is passed to `extract_and_validate(extractor=...)` without
changing cleaning, validation, parsing, storage, or LLM integration.

Readability check (`validation.py`): a page is readable if cleaned text length
> 100 chars. The document is rejected if `readable_pages / total_pages < 0.5`
or `total_text_length < 300`. Rejection raises `PdfUnreadableError`, which the
route maps to HTTP 422 with `detail.error_code == "pdf_unreadable"`. The frontend
shows the unreadable-PDF dialog on that code.

Flow after a readable upload (`SessionService.process_transcript`):

```text
extract+validate -> parse_study_plan (LLM parse, reused study_plan_parser)
                 -> validate_study_plan (deterministic rule check)
                 -> persist parsed plan + rule check into LangGraph session state
                 -> retain extracted text only in the local WizardFlow trace
                 -> return parsed plan + rule check
```

The parser LLM receives extracted PDF text as its unredacted `msg`, and
WizardFlow stores that `llm_input` locally. Raw text is not persisted in
LangGraph session state and is not passed to `answer_composer`; only the parsed
`StudyPlan` and deterministic `rule_check_result` continue through the session,
in line with "LLM parses -> Python validates -> LLM explains". The parsed plan
is persisted via `agent_app.update_state` so chat follow-ups (e.g. "is Telematik
counted?") can reference it.

PDF library: `pypdf` (already in `requirements.txt`). It was chosen over PyMuPDF
to avoid the AGPL license; the `PDFExtractor` interface keeps the choice swappable.

Frontend pieces (`frontend/src/app/consultant/components/`):

```text
TranscriptUpload.tsx     -> shared upload control (icon variant in Chat, button in Study Plan)
UnreadablePdfDialog.tsx  -> "This PDF appears to be unreadable..." dialog
chatMessages.ts          -> shared ChatMessage type + storage helpers + transcript->message builder
```

The Study Plan tab unmounts the Chat tab while active, so its upload writes the
result into the shared chat sessionStorage and lifts rule-check/plan state up;
the Chat tab rehydrates from storage when reselected.

## Program Rules Catalogue

Structured display rules live per degree:

```text
backend/app/domain/program_rules.py                        # shared models + render_rules_context()
backend/app/domain/degrees/<degree>/program_rules.py       # per-degree catalogue content
```

Purpose:

- Source for the frontend Degree Rules tab (selected via `?degree=`).
- Human-readable catalogue of degree-rule sections, items, sources, and related validation issue codes.
- Stable JSON projection through `GET /api/program-rules`.

Do not make `backend/knowledge_base/generated/degree_rules.md` the source for the frontend. That Markdown is RAG-facing generated documentation. The frontend should call the API and render structured JSON.

Ownership split:

```text
degrees/<d>/degree_rules.py    -> executable validation logic
degrees/<d>/program_rules.py   -> structured human-readable rule catalogue
degrees/<d>/prompts.py         -> RULES_CONTEXT rendered from that degree's catalogue
course_offerings.json          -> shared tagged course-offering source (per-degree projection)
module_catalog.md              -> optional RAG-ingested artifact for manual/future retrieval
frontend/services/api          -> API client only, no validation-rule ownership
```

If rule behavior changes, update in the affected degree package:

1. `degree_rules.py`
2. `program_rules.py`
3. focused tests (`test_rule_checker.py` for msc_informatik,
   `test_data_science_rules.py` for msc_data_science)

Re-ingesting RAG is no longer required for rule edits because the rule sources
are no longer ingested. Only `module_catalog.md` is in the Qdrant collection,
and Qdrant is not used by the active study-question graph.

The Softwareprojekt and Wissenschaftliches Arbeiten Wahlbereich caveats must stay visible in both validation and display rules.

## Frontend

Frontend work should use:

```text
Next.js App Router
React
TypeScript
Material UI
```

The frontend is exported statically. Caddy serves `frontend/out` directly in
production; `frontend-preview` is an optional local Docker profile backed by a
small Caddy image, not a Node.js runtime. Keep frontend edits inside
`fu_berlin_cs_consultant/frontend/`.

Expected first frontend structure:

```text
frontend/
  src/
    app/
      layout.tsx
      page.tsx
      consultant/
        page.tsx
        components/
          ConsultantShell.tsx
          ChatTab.tsx
          StudyPlanTab.tsx
          DegreeRulesTab.tsx
          SettingsTab.tsx
          CitationList.tsx
          RuleCheckPanel.tsx
          ModuleTable.tsx
    components/
    context/
      SettingsContext.tsx
      UsageContext.tsx
      DegreeContext.tsx
    services/
      api.ts
    theme/
      colors.ts
      theme.ts
    types/
      api.ts
```

Initial tabs:

```text
Chat
Study Plan
Degree Rules
Settings
```

Tab responsibilities:

- `Chat`: session creation, message send, assistant response, citations, and plan-check result summary.
- `Study Plan`: student-specific extracted plan, modules, LP totals, Wahlbereich data, and validation issues. This needs dedicated study-plan API endpoints before it can be complete.
- `Degree Rules`: read-only rendering of `GET /api/program-rules`.
- `Settings`: dark mode, request allowance, production-visible reset
  conversation, plus optional developer diagnostics.

Frontend conventions:

- Use MUI components and `sx` styling.
- Do not add Tailwind.
- Prefer theme tokens over hardcoded colors.
- Use icon buttons where an established icon exists.
- Keep the first screen as the actual consultant app, not a landing page.
- Keep SettingsContext as the frontend source of truth for dark mode.
- Keep UsageContext as the frontend source of truth for request allowance and
  runtime retention information.
- Keep DegreeContext as the frontend source of truth for the chosen degree
  (persisted in localStorage). The welcome dialog collects the choice with
  card-style toggle buttons; the header subtitle is the degree switcher.
  Switching with an active session opens `DegreeSwitchDialog`, which warns that
  chat/study-plan data is discarded and offers the chat download and the Study
  Plan print summary first. Confirmed switches delete the backend session,
  clear local chat state, and create the next session with the new degree.
- Keep `Reset conversation` visible when `NEXT_PUBLIC_ENABLE_DEV_TOOLS=false`;
  only API/session diagnostics, health details, and dummy data are developer-only.
- Keep API calls in `frontend/src/services/api.ts`.
- Keep shared TypeScript API contracts in `frontend/src/types/api.ts`.
- Do not put degree-rule validation logic in TypeScript. The frontend renders backend data and validation results.
- If i18n is added later, use `next-intl` and update all locale files together.

## RAG

Manual ingestion script:

```text
backend/scripts/ingest_resources.py
```

Run from `fu_berlin_cs_consultant/` after Docker services are running:

```bash
docker compose --profile legacy-rag up -d qdrant
docker compose --profile legacy-rag run --rm legacy-rag-ingest
```

Default collection:

```text
fu_cs_consultant_knowledge
```

Default embedding model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Generated knowledge artifacts:

```text
backend/knowledge_base/generated/degree_rules.md
backend/knowledge_base/generated/module_catalog.md
backend/knowledge_base/generated/module_catalog.json
```

If rule behavior changes, update deterministic code and the structured display
catalogue in `program_rules.py`; `RULES_CONTEXT` is rendered from that catalogue.
RAG ingestion is not required for active rule or course-offering answers.

`knowledge_base/generated/` is a generated retrieval corpus, not the frontend source of truth. The Degree Rules tab should use `program_rules.py` through `GET /api/program-rules`.

## LLM Providers

Configured in `backend/app/settings.py`.

Supported providers:

```text
LLM_PROVIDER=academiccloud   # hosted AcademicCloud API
LLM_PROVIDER=fu_ollama       # FU Ollama on cuda01 via auto SSH tunnel
LLM_PROVIDER=local_ollama    # Ollama running on the host machine
```

Each provider reads its own `<PROVIDER>_*` env vars (model, temperature,
timeout, etc.). The SSH tunnel for `fu_ollama` is started automatically
during app lifespan — there is no separate `USE_SSH` flag. SSH credentials
live under `FU_SSH_USER` / `FU_SSH_PASSWORD` in `.env.local`.

`fu_ollama` only works when the computer is connected to the FU Berlin VPN. If
the SSH tunnel or cuda01 connection fails, check VPN connectivity before
changing SSH credentials or provider code.

Use AcademicCloud sparingly. The configured AcademicCloud API key is registered
for another project too, so avoid unnecessary exploratory calls and prefer
`local_ollama` or `fu_ollama` for development/testing when practical.

Provider services:

```text
backend/app/services/academiccloud_service.py
backend/app/services/ollama_service.py
backend/app/services/model_service.py
backend/app/services/ssh_manager.py
```

Prompt convention (applies inside every degree's `prompts.py`):

- Internal LLM nodes use `DOMAIN_SCOPE`.
- Only `AnswerComposer` uses `ANSWER_IDENTITY`.
- Keep classifiers, parsers, and course-key selectors terse and task-specific.
- Degree-specific wording stays inside the degree package; nodes must not
  hardcode any degree's terminology.

## Verification

Compile check:

```bash
python -m compileall -q "fu_berlin_cs_consultant\backend\app" "fu_berlin_cs_consultant\backend\scripts"
```

Focused tests from `fu_berlin_cs_consultant/backend`:

```bash
uv run --isolated --python 3.12.10 --with-requirements requirements.txt --with pytest python -m pytest -q
```

Runtime checks, when Docker and credentials are available:

```bash
docker compose build backend
cd frontend && npm run build && cd ..
docker compose --profile frontend-preview build frontend
docker compose --profile frontend-preview up
curl http://localhost:3000/
curl http://localhost:8000/health
```

For production, first rebuild `frontend/out/` locally and deploy the updated
repository revision, then run the production Compose profile; only `backend`
and Caddy run. Use `docker compose logs -f backend caddy` when production
runtime behavior is unclear.
Use `docker compose --profile legacy-rag up -d qdrant` only when testing manual
legacy RAG ingestion.

The backend Dockerfile intentionally wraps apt update/install in timeouts. If apt times out, investigate Docker network access to Debian mirrors before changing Python dependencies.

Frontend checks from `fu_berlin_cs_consultant/frontend`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

## Documentation Expectations

When behavior changes, update the relevant docs:

- Agent routing or node responsibilities: `docs/agent-flow.md` and `docs/agent-flow.html`
- Study plan state/schema/persistence: `docs/study-plan-data.md`
- RAG sources/chunking/metadata: `docs/rag-ingestion.md`
- Frontend architecture/API assumptions: add or update `docs/frontend.md` once frontend scaffolding exists
- Setup/API commands: `README.md`
- Implementation checklist: `implementation.md`
