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

Semester coverage is not configured manually. The course selector derives
available semesters from `backend/app/domain/data/course_offerings.json`.

## Start

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
docker compose exec backend python scripts/ingest_resources.py
```

Only original files under `ressources/`:

```bash
docker compose exec backend python scripts/ingest_resources.py --skip-generated
```

The default ingestion includes:

- `ressources/*.txt`
- `ressources/*.pdf`
- `backend/knowledge_base/generated/*.md`

## API

Create a session:

```bash
curl -X POST http://localhost:5100/api/sessions
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
python -m pytest
```

The current tests cover deterministic rule checking, resource chunking, and pure routing helpers.

From `fu_berlin_cs_consultant/frontend`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```
