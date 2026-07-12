# RAG Ingestion

This document describes how the FU Berlin CS consultant builds its optional local RAG knowledge base.
The active `course_offering_question` graph path no longer uses Qdrant for
course/module answers; it uses exact lookup over
`backend/app/domain/data/course_offerings.json`. The `degree_question` path
skips lookup and answers from `RULES_CONTEXT`. The RAG code and ingestion script
remain available for future experiments and manual module-catalogue retrieval.

## Design Choice

Ingestion is manual only.

There is intentionally no API endpoint such as:

```text
POST /api/ingest
```

Reason:

- Ingestion mutates the vector database.
- It can be slow because it loads the embedding model.
- It is an admin/developer operation, not an app-user action.
- It should not be exposed without authentication.

## Source Files

Original resources live in:

```text
fu_berlin_cs_consultant/ressources/
```

Generated helper artifacts live in:

```text
fu_berlin_cs_consultant/backend/knowledge_base/generated/
```

Current generated artifacts:

```text
degree_rules.md
module_catalog.md
module_catalog.json
```

Only `module_catalog.md` is ingested into Qdrant. Everything else under
`ressources/` and `knowledge_base/generated/` is intentionally skipped because:

- Degree rules (`Informatik_Master_Ablauf.txt`, the Checkliste PDF, and the
  generated `degree_rules.md`) now live in the structured catalogue at
  `app.domain.degrees.msc_informatik.program_rules`; that degree's
  `prompts.RULES_CONTEXT` is rendered from the catalogue. Keeping them in RAG too would double up the source of truth and add
  retrieval latency for no gain.
- `module_catalog.json` is consumed directly by the deterministic Python
  lookup in `module_catalog.py` and does not need embedding.
- Current semester course offerings are not generated RAG artifacts. They live
  in `backend/app/domain/data/course_offerings.json` and are read directly by
  `app.domain.course_offerings`.

The allowlist is enforced by `INGEST_FILENAMES` in
`backend/scripts/ingest_resources.py`. Extend that set when adding a new
module-catalogue-style source.

## Manual Command

From `fu_berlin_cs_consultant/`:

The normal backend environment installs `backend/requirements.txt` and does
not include the embedding stack. Manual ingestion uses the optional
`backend/requirements-legacy-rag.txt`, which adds the CPU-only Torch build,
SentenceTransformer, and Qdrant client. Docker selects that dependency set
through the `legacy-rag` image target.

Qdrant is disabled by default in Docker Compose. Start the optional legacy RAG
profile before running ingestion:

```bash
docker compose --profile legacy-rag up -d qdrant
```

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest
```

To ingest only original files under `ressources/`:

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest \
  python scripts/ingest_resources.py --skip-generated
```

The script can also take a custom collection:

```bash
docker compose --profile legacy-rag run --rm legacy-rag-ingest \
  python scripts/ingest_resources.py --collection fu_cs_consultant_knowledge
```

For non-Docker experiments, create a separate environment so the production
runtime stays small:

```bash
cd backend
python -m venv .venv-legacy-rag
source .venv-legacy-rag/bin/activate
python -m pip install --no-cache-dir -r requirements-legacy-rag.txt
```

## Collection

The default Qdrant collection is:

```text
fu_cs_consultant_knowledge
```

Configured by:

```text
QDRANT_COLLECTION
```

The collection is rebuilt deterministically on every ingestion run:

```text
delete collection if it exists
create collection
embed all chunks
upsert all chunks
```

This avoids stale chunks after resources change.

## Embeddings

Default embedding model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Configured by:

```text
QDRANT_EMBEDDING_MODEL
QDRANT_VECTOR_SIZE
```

The default vector size is `384`.

The multilingual model is intentional because source content and user questions may be German or English.

## Supported File Types

The ingestion script supports:

- `.txt`
- `.md`
- `.pdf`

PDF extraction is implemented in:

```text
backend/scripts/extract_pdf.py
```

Text and Markdown loading/chunking is implemented in:

```text
backend/app/services/resource_loader.py
```

## Chunking

The loader normalizes text first:

- Windows line endings become `\n`.
- repeated spaces are collapsed.
- repeated blank lines are collapsed.

Then it splits by semantic headings where possible.

Examples of headings:

- `Randbedingungen`
- `Allgemeines:`
- checklist section headings such as `A. Bereich Informatik`
- numbered module-area headings

Long sections are split by paragraph with an approximate maximum chunk length.

## Chunk IDs

Chunk IDs are stable UUIDv5 values.

The ID input includes:

```text
source path
chunk position
PDF page, if any
section heading, if any
```

This means the same source content structure produces stable point IDs across rebuilds.

## Payload Metadata

Each Qdrant point stores:

```text
title
source
source_path
section_heading
page
position
content
content_hash
embedding_model
ingested_at
```

The removed legacy retrieval node previously turned this metadata into API citations:

```text
source
title
section_heading
page
score
```

## No Runtime Retrieval Node

Runtime Qdrant retrieval is currently not wired into
`backend/app/services/agent_graph_service.py`. The active course-offering path is:

```text
course_key_selector
  -> course_lookup
  -> answer_composer
```

Course lookup selects keys such as `sose26/technical/swp`, validates them
against `course_offerings.json`, and passes whole buckets to the answer
composer.

The former `retrieval.py` and `query_rewriter.py` agent nodes have been removed.
The remaining `VectorService` can still support explicit manual experiments,
but no active or inactive LangGraph node calls it. Manual callers choose their
own search limit and filtering behavior.

## Relationship To Deterministic Rules

RAG is optional and currently not used by the active graph for explanation or
grounding.

RAG is not the final authority for study-plan validation.

For `plan_check` messages (no Qdrant retrieval involved):

```text
study_plan_parser extracts structure
degree_rules.py validates deterministically
answer_composer explains the deterministic result, using RULES_CONTEXT rendered from program_rules.py
```

This separation matters because LP totals, seminar/project limits, Wahlbereich caveats, ungraded LP, Bachelor-module LP, and duplicate checks should be reproducible and testable.

## When To Re-Ingest

Run ingestion after:

- editing `module_catalog.md`
- adding a new file to `INGEST_FILENAMES` in `ingest_resources.py`
- changing chunking behavior
- changing the embedding model
- changing the Qdrant collection name

Degree-rule edits should go into deterministic Python rules
(`app.domain.degrees.<degree>.degree_rules`) and the structured human-readable
catalogue (`app.domain.degrees.<degree>.program_rules`). Each degree's
`prompts.RULES_CONTEXT` is rendered from its own `program_rules.py`. The generated `degree_rules.md` is no longer ingested, so a
re-ingest is not required after rule edits.

Editing `backend/app/domain/data/course_offerings.json` does not require
Qdrant ingestion. Restart or rebuild the backend container as needed so the
running Python process reads the changed JSON.
