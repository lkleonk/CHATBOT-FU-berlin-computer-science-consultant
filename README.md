![FU Berlin CS Consultant home page](ressources/home_page.png)

# LeoPunkt — FU Berlin CS Consultant

Full-stack prototype for a FU Berlin Master Informatik study consultant, named **LeoPunkt** (a nod to *Leistungspunkte* — the LP credits it helps you track).

The app answers questions from local resources in `ressources/` and can check a proposed study plan against deterministic 2014 Master Informatik rules. It includes a standalone Next.js frontend and a FastAPI backend. It reuses architecture patterns from the parent `llm_chatbot` project, but all code lives inside `fu_berlin_cs_consultant/`.

## Screenshots

Agent flow:

![Agent flow](ressources/screenshot_agent_flow.png)

Study plan check (visualizes the proposed study plan, then validates it against the deterministic 2014 Master Informatik rules and flags missing credits or unmet requirements):

![Study plan](ressources/screenshot_study_plan.png)

## Scope

- No Postgres in phase 1.
- Manual RAG ingestion only; active course-offering lookup is exact JSON lookup, not Qdrant.
- LLM provider can be AcademicCloud or FU/local Ollama.
- Answers are advisory. Official FU Berlin documents and the examination office remain authoritative for real study decisions.

## Project Structure

```text
fu_berlin_cs_consultant/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py              # App entrypoint
│   │   ├── routes.py            # API routes
│   │   ├── models.py            # Pydantic models
│   │   ├── prompts.py           # LLM prompts
│   │   ├── settings.py          # Config
│   │   ├── domain/              # Degree rules, course offerings, module catalog, study plan logic
│   │   └── services/            # LLM providers, vector store, agent graph
│   │       ├── nodes/           # Agent graph nodes (course lookup, rule checker, ...)
│   │       └── states/          # Agent graph state
│   ├── knowledge_base/generated/ # Generated rules & module catalog
│   ├── scripts/                 # PDF extraction & resource ingestion
│   ├── tests/                   # Pytest suite
│   └── Dockerfile
├── frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Pages & consultant UI components
│   │   ├── context/             # React context (settings)
│   │   ├── services/            # API client
│   │   ├── theme/               # MUI theme & colors
│   │   └── types/               # Shared API types
│   ├── public/                  # Static assets
│   └── Dockerfile
├── ressources/                  # Source documents & screenshots
├── docs/                        # Project docs & diagrams
├── docker-compose.yml
└── .env.example
```

## Services

```text
Next.js frontend -> http://localhost:3000/consultant
FastAPI backend  -> http://localhost:5100
Qdrant           -> optional legacy-rag profile, localhost:6335 on host when enabled
```

The normal backend installation uses `backend/requirements.txt` and does not
install Torch, SentenceTransformer, or Qdrant. Those packages are isolated in
`backend/requirements-legacy-rag.txt` and are installed only by the optional
manual-ingestion environment or Docker target.

## Environment

Create `.env` from `.env.example` and fill in the provider you want. Docker Compose uses `.env` as the container env file.

```bash
cp .env.example .env
```

Pick one provider via `LLM_PROVIDER`. Each provider reads its own `<PROVIDER>_*` vars; the others are ignored.

AcademicCloud (hosted API):

```env
LLM_PROVIDER=academiccloud
ACADEMICCLOUD_MODEL=qwen3-235b-a22b
# ACADEMICCLOUD_API_KEY goes in .env.local
```

FU Ollama (cuda01 via auto SSH tunnel — no extra flag needed):

```env
LLM_PROVIDER=fu_ollama
FU_OLLAMA_MODEL=llama3.2
FU_SSH_HOST=cuda01.imp.fu-berlin.de
FU_SSH_PORT=22
# FU_SSH_USER and FU_SSH_PASSWORD go in .env.local
```

Local Ollama (running on the host machine):

```env
LLM_PROVIDER=local_ollama
LOCAL_OLLAMA_HOST=http://host.docker.internal:11434
LOCAL_OLLAMA_MODEL=llama3.2
```

Optional agent-flow tuning:

```env
AGENT_COURSE_SELECTOR_HISTORY_TURNS=2
AGENT_COURSE_SELECTOR_MAX_KEYS=20
AGENT_COURSE_SELECTOR_INCLUDE_SEMESTERS_NOTE=true
AGENT_ANSWER_COMPOSER_HISTORY_TURNS=4
```

Daily usage limits:

```env
DAILY_LLM_INVOCATIONS=200
DAILY_USER_ACTIONS=100
```

The LLM limit is global. Every call made through `ModelService` consumes one
invocation, so one chat action can consume multiple invocations. The user-action
limit applies per client IP to chat messages and transcript uploads. Creating or
deleting a session, reading program rules, and checking health do not consume
user actions.

`GET /api/usage` exposes the current client-IP action allowance without
consuming it. Successful chat and transcript responses also carry
`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and
`X-RateLimit-Scope` headers. The frontend shows a clickable allowance chip and
warns once per reset period when ten or fewer actions remain.

These counters are deliberately process-local Python state. They reset at
00:00 UTC and whenever the backend restarts. Run a single backend worker if the
configured numbers must remain the effective limits; each additional process
would have its own counters.

In-memory session retention:

```env
SESSION_INACTIVITY_TTL_SECONDS=172800
SESSION_CLEANUP_INTERVAL_SECONDS=300
```

Sessions are deleted after 48 hours without a message or transcript upload.
Cleanup runs opportunistically during later session activity, so no scheduler is
required. The production-visible Settings `Reset conversation` button calls
`DELETE /api/sessions/{session_id}`
before clearing browser state. Session cleanup does not delete WizardFlow trace
files; trace retention remains a separate operational concern.

Frontend developer diagnostics are build-time gated:

```env
NEXT_PUBLIC_ENABLE_DEV_TOOLS=false
```

When disabled, API/session diagnostics, health details, and dummy data are
hidden. Request allowance, chat download, and `Reset conversation` remain
available. The chat download is produced locally as Markdown and never sent to
the backend.

Semester coverage is not configured manually. The course selector derives
available semesters from `backend/app/domain/data/course_offerings.json`.

## Start

Backend only, without Docker (Python 3.11 or 3.12):

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 5100 --workers 1
```

This installs only the active API/agent runtime. Do not use
`requirements-legacy-rag.txt` on a normal deployment server.

Full stack with Docker:

```bash
docker compose up --build
```

For isolated builds while diagnosing dependency installs:

```bash
docker compose build backend
docker compose build frontend
docker compose up
```

Follow runtime logs after services start:

```bash
docker compose logs -f backend frontend
```

The backend Dockerfile has timeouts around apt:

- package index update: 300 seconds
- system dependency install: 600 seconds

If one of those times out, the problem is Debian package network access from Docker rather than Python dependency resolution.

Frontend:

```text
http://localhost:3000/consultant
```

API docs:

```text
http://localhost:5100/docs
```

## WizardFlow Traces

WizardFlow tracing is enabled by default. Each chat request and transcript
upload receives a new UUID, and each active agent node writes payloads into a
JSONL trace under `backend/traces/`. Docker persists `/app/traces` to that host
directory.

LLM-backed nodes record:

```text
llm_input  -> {"prompt": "...", "msg": "..."}
llm_output -> raw model response
llm_error  -> exception type and message, when a fallback is used
```

Deterministic nodes record `node_input` and `node_output`. Trace failures are
logged but do not fail consultant requests.

Configuration:

```env
WIZARDFLOW_ENABLED=true
WIZARDFLOW_OUTPUT_DIR=traces
WIZARDFLOW_FILE_PREFIX=fu_cs_consultant
```

For a university production deployment that promises session-only temporary
storage, set `WIZARDFLOW_ENABLED=false`. When tracing is enabled, the welcome
dialog discloses that unredacted diagnostic files may outlive in-memory session
state.

From `backend/`, inspect a generated trace with:

```bash
wizardflow ui traces/<trace-file>.jsonl
wizardflow json traces/<trace-file>.jsonl
```

Trace files contain unredacted system prompts, chat messages, and extracted
transcript text. Treat `backend/traces/` as sensitive local data; it is excluded
from Git.

## Manual Ingestion

Ingestion rebuilds the Qdrant collection from local files. There is intentionally no public ingest endpoint.
Qdrant is currently not wired into the active study-question graph; course
offerings are read directly from `backend/app/domain/data/course_offerings.json`.

Qdrant is disabled during normal `docker compose up`. Start it only when you
want to run the legacy/manual ingestion workflow:

```bash
docker compose --profile legacy-rag up -d qdrant
```

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest
```

Only original files under `ressources/`:

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest \
  python scripts/ingest_resources.py --skip-generated
```

The optional ingestion image installs `backend/requirements-legacy-rag.txt`,
including the CPU-only Torch build, SentenceTransformer, and Qdrant client. The
normal backend image remains runtime-only.

The default ingestion includes:

- `ressources/*.txt`
- `ressources/*.pdf`
- `backend/knowledge_base/generated/*.md`

## API

Create a session:

```bash
curl -X POST http://localhost:5100/api/sessions
```

Delete a session and its in-memory LangGraph state:

```bash
curl -X DELETE http://localhost:5100/api/sessions/<session-id>
```

Read the current client request allowance and retention information:

```bash
curl http://localhost:5100/api/usage
```

Ask a question:

```bash
curl -X POST http://localhost:5100/api/sessions/<session-id>/message \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"Wie viele LP brauche ich im Anwendungsbereich?\"}"
```

Check a study plan:

```bash
curl -X POST http://localhost:5100/api/sessions/<session-id>/message \
  -H "Content-Type: application/json" \
  -d "{\"content\":\"Bitte pruefe meinen Studienplan mit Vertiefung Praktische Informatik: Softwareprojekt Praktische Informatik B 10 LP, Wissenschaftliches Arbeiten Praktische Informatik A 5 LP, Projektmanagement 5 LP, Kuenstliche Intelligenz 5 LP, Datenbanktechnologie 5 LP, Rechnersicherheit 10 LP, Algorithmische Geometrie 10 LP, Modelchecking 10 LP, Betriebssysteme 10 LP, Wissenschaftliches Arbeiten Technische Informatik A 5 LP, Mobilkommunikation 5 LP, Anwendungsmodul A 10 LP.\"}"
```

Health:

```bash
curl http://localhost:5100/health
```

## Tests

From `fu_berlin_cs_consultant/backend`:

```bash
uv run --isolated --python 3.12.10 --with-requirements requirements.txt --with pytest python -m pytest -q
```

The current tests cover deterministic rule checking, resource chunking, and pure routing helpers.

From `fu_berlin_cs_consultant/frontend`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```
