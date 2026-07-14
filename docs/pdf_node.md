# PDF Attachment Node

This document describes a planned first implementation for letting users drag and drop a PDF into the chat and ask the consultant about it.

The first version intentionally supports only PDFs with machine-readable text. OCR is out of scope.

## Goals

- Let a user attach a PDF to an existing chat session.
- Extract embedded text from the PDF algorithmically.
- Make the extracted text available to the current session's agent flow.
- Allow the existing study-plan parser and deterministic rule checker to use extracted PDF text when the PDF contains a study plan.
- Keep uploaded PDFs session-scoped and temporary.

## Non-Goals

- Do not add a public ingestion endpoint.
- Do not persist uploaded PDFs outside their session processing flow.
- Do not modify files under `ressources/`.
- Do not use OCR in the first implementation.
- Do not trust the LLM for final LP validation.
- Do not put degree-rule validation logic in the frontend.

## User Experience

The Chat tab should support drag and drop for PDF files.

Expected behavior:

```text
User drops a PDF
  -> frontend uploads it for the active session
  -> backend extracts text
  -> frontend shows the attached file state
  -> user asks a question or requests a study-plan check
  -> backend uses the extracted PDF text as temporary session context
```

The user should be able to continue the chat after upload. The PDF should not become a permanent source for other users or future sessions.

If the PDF has no useful embedded text, the backend should return a clear error:

```text
This PDF does not contain enough machine-readable text. It may be scanned. OCR is not enabled yet.
```

## API Shape

The preferred API is session-scoped:

```text
POST /api/sessions/{session_id}/attachments
```

Request:

```text
multipart/form-data
file: PDF
```

Response:

```json
{
  "attachment_id": "att_...",
  "filename": "study-plan.pdf",
  "content_type": "application/pdf",
  "page_count": 4,
  "extracted_text_chars": 12000,
  "status": "ready"
}
```

This is not a global ingestion endpoint. It does not update the canonical course catalogue.

The existing message endpoint can then reference session attachments implicitly:

```text
POST /api/sessions/{session_id}/message
```

Optional future extension:

```json
{
  "message": "Check the study plan from the uploaded PDF.",
  "attachment_ids": ["att_..."]
}
```

For the first version, using all ready attachments from the active session is sufficient.

## Backend Components

Suggested new files:

```text
backend/app/services/pdf_text_extractor.py
backend/app/services/attachment_service.py
backend/app/services/nodes/attachment_context.py
```

Suggested model additions:

```text
backend/app/models.py
```

Possible response models:

```python
class AttachmentResponse(BaseModel):
    attachment_id: str
    filename: str
    content_type: str
    page_count: int
    extracted_text_chars: int
    status: Literal["ready", "rejected"]
```

The attachment service should own:

- file type validation
- size limits
- PDF text extraction
- per-session attachment storage
- quality checks for extracted text

## PDF Text Extraction

Use an algorithmic extractor first. The implementation uses **`pypdf`** (already
in `requirements.txt`). It was chosen over `PyMuPDF` — which is usually stronger
for layout-heavy PDFs but adds a native dependency — deliberately to avoid the
AGPL license. The `PDFExtractor` interface keeps the choice swappable, so a
future OCR or PyMuPDF extractor can subclass it and be passed to
`extract_and_validate(extractor=...)` without changing cleaning, validation,
parsing, storage, or LLM integration.

Extraction flow:

```text
validate content type and file extension
  -> read PDF bytes
  -> extract text per page
  -> normalize whitespace
  -> run text-quality checks
  -> store extracted text in session memory
```

Quality checks should include:

- minimum total extracted characters
- minimum average characters per non-empty page
- presence of recognizable words
- optional study-plan signals such as `LP`, `Modul`, `Masterarbeit`, `Note`, `Wahlbereich`

These checks should decide whether the PDF is usable. They should not decide whether a study plan is valid.

## Agent Flow Integration

The existing flow is:

```text
START
  -> ScopeClassifier
      -> off_topic                -> OfftopicReply -> END
      -> degree_question          -> AnswerComposer -> END
      -> course_offering_question -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check               -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

Planned first integration:

```text
START
  -> ScopeClassifier
      -> off_topic                -> OfftopicReply -> END
      -> degree_question          -> AttachmentContext -> AnswerComposer -> END
      -> course_offering_question -> AttachmentContext -> CourseKeySelector -> CourseLookup -> AnswerComposer -> END
      -> plan_check               -> AttachmentContext -> StudyPlanParser -> RuleChecker -> AnswerComposer -> END
```

`AttachmentContext` should be deterministic. It should not call an LLM.

Responsibilities:

- Load ready attachments for the current session.
- Build a bounded text context from extracted PDF text.
- Add that text to graph state.
- Preserve source metadata such as filename and page numbers when available.

## State Additions

The graph state could add:

```text
attachments
attachment_context
attachment_citations
```

Possible meanings:

| State key | Producer | Consumer |
|---|---|---|
| `attachments` | API/session service | `attachment_context` |
| `attachment_context` | `attachment_context` | `study_plan_parser`, `answer_composer` |
| `attachment_citations` | `attachment_context` | API response, `answer_composer` |

For a plan check, `StudyPlanParser` should parse from the latest user message plus `attachment_context`.

For a normal study question, `AnswerComposer` should use exact course-offering
lookup context plus attachment context, while clearly distinguishing
uploaded-document facts from official study-rule facts.

## Validation Principle

The existing rule remains unchanged:

```text
LLM parses -> Python validates -> LLM explains
```

For PDFs:

```text
PDF text extraction -> LLM parses study plan -> Python validates -> LLM explains
```

The PDF node may extract and format text, but it must not make final degree-rule decisions.

## Storage

Phase 1 should store attachments in memory only, consistent with the current `MemorySaver` session model.

Implications:

- attachments are lost when the backend restarts
- attachments are not shared across sessions
- no database or object storage is required
- no generated knowledge-base files are changed

If persistence is added later, it should be explicit and session-scoped.

## Frontend Implementation

Frontend work should stay under:

```text
frontend/
```

Suggested files:

```text
frontend/src/app/consultant/components/ChatTab.tsx
frontend/src/services/api.ts
frontend/src/types/api.ts
```

The Chat tab should add:

- drag-and-drop PDF upload
- file picker fallback
- upload progress state
- success/error state
- attached-file display
- disabled state while no session exists

The API client should add:

```ts
uploadSessionAttachment(sessionId: string, file: File): Promise<AttachmentResponse>
```

The frontend should not parse PDF content and should not validate degree rules.

## Limits And Safety

Recommended first-version limits:

- PDF only
- one or a small number of attachments per session
- maximum file size, for example 10 MB
- maximum page count, for example 30 pages
- maximum extracted text passed into the graph
- reject encrypted PDFs
- reject empty or unreadable PDFs

The answer composer should avoid treating uploaded PDFs as official rules.
Official rule answers should still rely on `RULES_CONTEXT` rendered from
`program_rules.py`, exact local lookup where relevant, and deterministic
validation.

## Testing

Backend tests should cover:

- PDF upload rejects non-PDF files
- PDF upload rejects oversized files
- text extraction succeeds for a simple text PDF
- text extraction rejects an empty/scanned-style PDF
- session attachment context is available to message processing
- plan-check messages can use attachment context
- no catalogue mutation is triggered

Frontend tests or manual checks should cover:

- drag-and-drop upload
- file picker upload
- disabled upload before session creation
- upload error display
- successful attached-file display

## Implementation Phases

### Phase 1: Backend Attachment Upload

- Add session-scoped attachment endpoint.
- Add PDF validation and native text extraction.
- Store extracted text in session memory.
- Return attachment metadata.

### Phase 2: Agent Graph Context

- Add `AttachmentContext` node.
- Add graph state keys for attachment context.
- Include attachment text in `StudyPlanParser` and `AnswerComposer` inputs.
- Keep `RuleChecker` unchanged.

### Phase 3: Frontend Drag And Drop

- Add PDF drop zone to Chat tab.
- Add API client method.
- Show upload and attachment states.
- Let chat messages use the active session's uploaded PDFs.

### Phase 4: Hardening

- Add text-size trimming with clear truncation metadata.
- Add page-aware citations for uploaded PDFs if extractor support is good enough.
- Improve table-heavy PDF extraction if needed.
- Add OCR only as a later explicit feature.

## Open Decisions

- Whether the message endpoint should use all session attachments or explicit `attachment_ids`.
- Exact file-size and page-count limits.
- Whether extracted text should be stored inside LangGraph state or in a separate session attachment store referenced by state.
