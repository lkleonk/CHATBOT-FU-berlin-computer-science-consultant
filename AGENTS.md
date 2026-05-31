# AGENTS.md

Instructions for agents working in `fu_berlin_cs_consultant/`.

## Hard Rules

- Do not use Git, except for read-only operations like `git diff`, `git status`, `git log`, and `git show`.
- Do not edit files outside `fu_berlin_cs_consultant/`.
- Do not add a public ingestion endpoint.
- Keep original files under `ressources/` untouched unless the user explicitly asks to update source material.
- Frontend work is allowed only inside `fu_berlin_cs_consultant/frontend/`.

## Project Purpose

This is a FU Berlin Master Informatik study consultant with a backend-first architecture and a standalone Next.js frontend.

It answers questions using exact local course-offering lookup plus rules in prompts, while preserving optional local RAG code for future/manual retrieval experiments. It validates proposed study plans with deterministic Python rules. The LLM may parse and explain, but the LLM must not be trusted for final LP validation.

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
      prompts.py
      settings.py
      domain/
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
      context/
      services/
      theme/
      types/
```

Technical docs:

```text
docs/study-plan-data.md
docs/agent-flow.md
docs/rag-ingestion.md
docs/agent-flow.html
```

## Backend API

Current public API:

```text
GET  /health
GET  /api/program-rules
POST /api/sessions
POST /api/sessions/{session_id}/message
POST /api/sessions/{session_id}/transcript
```

No `POST /api/ingest` route should exist.

`POST /api/sessions/{session_id}/transcript` accepts a multipart PDF upload
(field name `file`). See the "PDF Transcript Upload" section.

`GET /api/program-rules` returns the structured display catalogue for the frontend Degree Rules tab. It should not require Qdrant, embeddings, LangGraph, or an LLM to answer.

## Docker

`docker-compose.yml` starts:

```text
frontend -> http://localhost:3000/consultant
backend  -> http://localhost:5100
```

Qdrant is behind the optional `legacy-rag` Compose profile. Normal
`docker compose up` should not start Qdrant. Use
`docker compose --profile legacy-rag up -d qdrant` only for manual legacy RAG
ingestion or retrieval experiments.

Compose uses `.env` as the backend env file. Keep `.env.example` aligned when adding required runtime variables.

The frontend image is built from `frontend/Dockerfile`. The browser-facing API base URL is passed as:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:5100
```

This value is intentionally host-facing because the JavaScript runs in the user's browser, not inside the Docker network.

## Agent Flow

Implemented in `backend/app/services/agent_graph_service.py`.

```text
START
  -> ScopeClassifier
      -> off_topic      -> OfftopicReply -> END
      -> study_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check     -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

Degree rules reach the system prompt through `app.prompts.RULES_CONTEXT`, which
is rendered from `backend/app/domain/program_rules.py`. The `plan_check` path
does not need retrieval before parsing. Course-offering lookup on the
`study_question` path reads exact buckets from
`backend/app/domain/data/course_offerings.json`, using keys like
`sose26/technical/swp`. Qdrant retrieval code remains in the repository but is
not wired into the active graph.

`MemorySaver` is used for phase 1, so session state is in memory and lost on backend restart.

Agent-flow tuning lives in `backend/app/services/agent_config.py`. Current env
knobs include:

```text
AGENT_COURSE_SELECTOR_HISTORY_TURNS
AGENT_COURSE_SELECTOR_MAX_KEYS
AGENT_COURSE_SELECTOR_INCLUDE_SEMESTERS_NOTE
AGENT_ANSWER_COMPOSER_HISTORY_TURNS
```

Do not duplicate available semesters in settings. The course selector derives
semester coverage from `backend/app/domain/data/course_offerings.json`.

## Study Plan Validation

Core deterministic code:

```text
backend/app/domain/study_plan.py
backend/app/domain/module_catalog.py
backend/app/domain/degree_rules.py
backend/app/domain/program_rules.py
```

Key principle:

```text
LLM parses -> Python validates -> LLM explains
```

The rule checker currently handles:

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
                 -> discard the PDF text; return parsed plan + rule check
```

The raw PDF text is never injected into the LLM context. The LLM only ever sees
the validated `parsed_study_plan` (module list) and the deterministic
`rule_check_result`, in line with "LLM parses -> Python validates -> LLM
explains". The parsed plan is persisted via `agent_app.update_state` so chat
follow-ups (e.g. "is Telematik counted?") can reference it. `answer_composer`
now receives the parsed plan alongside the rule-check result.

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

Structured display rules live in:

```text
backend/app/domain/program_rules.py
```

Purpose:

- Source for the frontend Degree Rules tab.
- Human-readable catalogue of degree-rule sections, items, sources, and related validation issue codes.
- Stable JSON projection through `GET /api/program-rules`.

Do not make `backend/knowledge_base/generated/degree_rules.md` the source for the frontend. That Markdown is RAG-facing generated documentation. The frontend should call the API and render structured JSON.

Ownership split:

```text
degree_rules.py        -> executable validation logic
program_rules.py       -> structured human-readable rule catalogue and prompt projection
prompts.py RULES_CTX   -> imports rendered compact rules from program_rules.py
course_offerings.json  -> active exact course-offering lookup source
module_catalog.md      -> optional RAG-ingested artifact for manual/future retrieval
frontend/services/api  -> API client only, no validation-rule ownership
```

If rule behavior changes, update:

1. `degree_rules.py`
2. `program_rules.py`
3. focused tests

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

The frontend is now scaffolded and served by Docker Compose. Keep frontend edits inside `fu_berlin_cs_consultant/frontend/`.

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
- `Settings`: dark mode plus developer tools such as session ID, reset session, backend health, and API base URL.

Frontend conventions:

- Use MUI components and `sx` styling.
- Do not add Tailwind.
- Prefer theme tokens over hardcoded colors.
- Use icon buttons where an established icon exists.
- Keep the first screen as the actual consultant app, not a landing page.
- Keep SettingsContext as the frontend source of truth for dark mode.
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
docker compose exec backend python scripts/ingest_resources.py
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

Provider services:

```text
backend/app/services/academiccloud_service.py
backend/app/services/ollama_service.py
backend/app/services/model_service.py
backend/app/services/ssh_manager.py
```

Prompt convention:

- Internal LLM nodes use `DOMAIN_SCOPE`.
- Only `AnswerComposer` uses `ANSWER_IDENTITY`.
- Keep classifiers, parsers, and course-key selectors terse and task-specific.

## Verification

Compile check:

```bash
python -m compileall -q "fu_berlin_cs_consultant\backend\app" "fu_berlin_cs_consultant\backend\scripts"
```

Focused tests from `fu_berlin_cs_consultant/backend`:

```bash
uv run --with pytest --with pydantic --with python-dotenv --with fastapi --with httpx --with uvicorn --with pypdf --with python-multipart python -m pytest -q
```

Runtime checks, when Docker and credentials are available:

```bash
docker compose build backend
docker compose build frontend
docker compose up
curl http://localhost:3000/consultant
curl http://localhost:5100/health
```

Use `docker compose logs -f backend frontend` when runtime behavior is unclear.
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
