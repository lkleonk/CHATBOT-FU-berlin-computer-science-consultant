# AGENTS.md

Instructions for agents working in `fu_berlin_cs_consultant/`.

This file is the lean core: hard rules, orientation, and how to verify. Deep
per-subsystem reference lives in `docs/` — see the **Reference** index at the
bottom and read the relevant doc on demand rather than assuming.

## Hard Rules

- Do not use Git, except for read-only operations like `git diff`, `git status`, `git log`, and `git show`.
- Do not edit files outside `fu_berlin_cs_consultant/`.
- Do not add a public ingestion endpoint. There must be no `POST /api/ingest` route.
- Keep original files under `ressources/` untouched unless the user explicitly asks to update source material.
- Frontend work is allowed only inside `fu_berlin_cs_consultant/frontend/`.

## Project Purpose

Public website: `https://cs-modulio.com`

A FU Berlin study consultant for multiple degree programs, with a backend-first
architecture and a standalone Next.js frontend. Supported degrees live in a
registry (`backend/app/domain/degrees/`): currently `msc_informatik` and
`msc_data_science`. It answers questions using exact local course-offering lookup
plus rules in prompts, and validates proposed study plans with deterministic
per-degree Python rules. The core principle is **LLM parses → Python validates →
LLM explains**: the LLM may parse and explain, but must not be trusted for final
LP validation. Every session is bound to exactly one degree; the LLM never
chooses or infers the degree. The Course Registry is a second, read-only
consumer of the degree-scoped course-offering projection; it never reads source
JSON in the frontend or calls the LLM. See `docs/domain-model.md` for the degree
registry and data layers.

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
        data/courses.json              # shared canonical courses
        data/degree_modules/           # degree-specific credit mappings
        data/course_offerings/         # one JSON file per semester
        degrees/
          __init__.py           # registry: list_degrees(), get_degree(), DEFAULT_DEGREE_ID
          definition.py         # DegreeDefinition + DegreePrompts contract
          msc_informatik/       # prompts.py, degree_rules.py, program_rules.py
          msc_data_science/     # + module_catalog.py (canonical checklist modules)
      services/
      pdf/
    scripts/
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

There is no `backend/app/prompts.py`. Prompts are per-degree modules
(`domain/degrees/<degree>/prompts.py`) exposed through `DegreeDefinition.prompts`;
nodes resolve them via `degree_for(state)` in `services/nodes/utils.py`.

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

## Verification

Compile check:

```bash
python -m compileall -q "fu_berlin_cs_consultant\backend\app" "fu_berlin_cs_consultant\backend\scripts"
```

Focused tests from `fu_berlin_cs_consultant/backend`:

```bash
uv run --isolated --python 3.12.10 --with-requirements requirements.txt --with pytest python -m pytest -q
```

Frontend checks from `fu_berlin_cs_consultant/frontend`:

```bash
npm run lint
npx tsc --noEmit
npm run build
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

Deployment/build gotchas (static export, Caddy, apt timeouts) are in
`docs/deployment.md`.

## Documentation Expectations

When behavior changes, update the relevant docs:

- Agent routing or node responsibilities: `docs/agent-flow.md` and `docs/agent-flow.html`
- Study plan state/schema/persistence: `docs/study-plan-data.md`
- Domain model (degrees, course data, program rules): `docs/domain-model.md`
- PDF transcript pipeline: `docs/pdf_node.md`
- Backend API surface/contracts: `docs/backend-api.md`
- Frontend architecture/conventions: `docs/frontend.md`
- LLM providers/model choice: `docs/llm-providers.md`
- Deployment/Docker/Caddy: `docs/deployment.md`
- Setup/API commands: `README.md`
- Implementation checklist: `implementation.md`

## Reference

Read the relevant doc before working on a subsystem; the code is always the
final source of truth for exact routes, schemas, and rule lists.

| Topic | Doc |
|---|---|
| Agent graph flow, nodes, routing, tracing | `docs/agent-flow.md` (+ `.html`) |
| Backend API routes, sessions, quotas, lifecycle | `docs/backend-api.md` |
| Degree registry, course-offering data, program rules, validation ownership | `docs/domain-model.md` |
| Study plan schemas, storage, data flow | `docs/study-plan-data.md` |
| M.Sc. Data Science degree structure | `docs/data_science_master.md` |
| PDF transcript upload pipeline | `docs/pdf_node.md` |
| Frontend architecture, state, tabs, conventions | `docs/frontend.md` |
| LLM providers, model choice, prompt conventions | `docs/llm-providers.md` |
| Docker / Compose / Caddy / static export | `docs/deployment.md` |
