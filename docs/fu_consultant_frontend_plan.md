# FU Consultant Frontend Plan

DO NOT USE GIT.

This plan covers the frontend for `fu_berlin_cs_consultant/`.

The frontend must live in:

```text
fu_berlin_cs_consultant/frontend/
```

The existing parent project frontend at `frontend/` is inspiration only. Do not import from it, edit it, or couple the consultant frontend to it.

## Goal

Build a standalone Next.js + Material UI frontend for the FU Berlin Master Informatik consultant.

The first usable screen should be the consultant app itself, not a landing page.

Initial tabs:

```text
Chat | Study Plan | Degree Rules | Settings
```

## Design Principles

- [ ] Use Next.js App Router.
- [ ] Use React + TypeScript.
- [ ] Use Material UI.
- [ ] Do not use Tailwind.
- [ ] Keep the UI quiet, utilitarian, and suited for repeated consultation work.
- [ ] Use the existing `llm_chatbot/frontend/src/app/patient-portal/page.tsx` only as layout inspiration.
- [ ] Use a fixed full-height tab shell with stable scrolling areas.
- [ ] Keep the first viewport focused on the actual consultant workflow.
- [ ] Avoid marketing-style hero sections.
- [ ] Avoid frontend-owned degree-rule validation logic.
- [ ] Let the backend remain the source of truth for rule checks and display rules.

## Phase 1: Frontend Scaffold

- [ ] Create `fu_berlin_cs_consultant/frontend/`.
- [ ] Add Next.js project files:
  - [ ] `package.json`
  - [ ] `next.config.ts`
  - [ ] `tsconfig.json`
  - [ ] `.gitignore` only if needed locally, without using git
- [ ] Install dependencies:
  - [ ] `next`
  - [ ] `react`
  - [ ] `react-dom`
  - [ ] `@mui/material`
  - [ ] `@mui/icons-material`
  - [ ] `@emotion/react`
  - [ ] `@emotion/styled`
  - [ ] `typescript`
  - [ ] `eslint` / Next lint setup if practical
- [ ] Add base source structure:

```text
frontend/
  src/
    app/
      layout.tsx
      page.tsx
      consultant/
        page.tsx
        components/
    components/
    context/
    services/
    theme/
    types/
```

## Phase 2: Theme And Settings Foundation

- [ ] Add `src/context/SettingsContext.tsx`.
- [ ] Store dark mode in localStorage.
- [ ] Expose:
  - [ ] `darkMode`
  - [ ] `toggleDarkMode`
- [ ] Add `src/theme/colors.ts`.
- [ ] Add `src/theme/theme.ts`.
- [ ] Use MUI `ThemeProvider` in `src/app/layout.tsx`.
- [ ] Keep the first version settings minimal:
  - [ ] dark mode
  - [ ] developer diagnostics
- [ ] Keep language settings out of the initial shell unless they are implemented through the multilingual UI phase.
- [ ] Do not add font-size settings yet unless explicitly requested.

## Phase 3: API Client And Types

- [ ] Add `src/services/api.ts`.
- [ ] Use an env-based backend URL:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:5100
```

- [ ] Add `src/types/api.ts`.
- [ ] Add TypeScript types matching backend responses:
  - [ ] `SessionResponse`
  - [ ] `Citation`
  - [ ] `RuleIssue`
  - [ ] `RuleCheckResult`
  - [ ] `ModelReply`
  - [ ] `HealthResponse`
  - [ ] `ProgramRuleSource`
  - [ ] `ProgramRuleItem`
  - [ ] `ProgramRuleSection`
  - [ ] `ProgramRulesCatalogue`
- [ ] Add API functions:
  - [ ] `createSession()`
  - [ ] `sendMessage(sessionId, content)`
  - [ ] `getProgramRules()`
  - [ ] `getHealth()`
- [ ] Add future API placeholders only as TODOs, not fake implementations:
  - [ ] `getStudyPlan(sessionId)`
  - [ ] `updateStudyPlan(sessionId, plan)`
  - [ ] `checkStudyPlan(sessionId)`

## Phase 4: App Shell

- [ ] Add `src/app/page.tsx` redirecting or rendering the consultant page.
- [ ] Add `src/app/consultant/page.tsx`.
- [ ] Add `ConsultantShell.tsx`.
- [ ] Use top MUI tabs:

```text
Chat
Study Plan
Degree Rules
Settings
```

- [ ] Keep layout full-height.
- [ ] Keep tab bar fixed at the top of the app shell.
- [ ] Ensure tab content has stable scrolling and does not resize the whole page.
- [ ] Persist active tab only if useful; otherwise default to Chat.

## Phase 5: Chat Tab

- [ ] Add `ChatTab.tsx`.
- [ ] Add shared chat components if useful:
  - [ ] `MessageList.tsx`
  - [ ] `ChatInput.tsx`
  - [ ] `CitationList.tsx`
  - [ ] `RuleCheckPanel.tsx`
- [ ] Persist `session_id` in `sessionStorage`.
- [ ] Persist chat messages in `sessionStorage` for the current browser session.
- [ ] On first message, call:

```text
POST /api/sessions
```

- [ ] For each user message, call:

```text
POST /api/sessions/{session_id}/message
```

- [ ] Render:
  - [ ] user messages
  - [ ] assistant replies
  - [ ] loading state
  - [ ] errors
  - [ ] citations returned by RAG
  - [ ] rule-check result summary when present
- [ ] Keep the input pinned at the bottom of the Chat tab.
- [ ] Do not include medical widgets from the parent app.
- [ ] Do not include pain sliders, body maps, emergency dialogs, navigation, or SAMPLER UI.

## Phase 6: Degree Rules Tab

- [ ] Add `DegreeRulesTab.tsx`.
- [ ] Fetch:

```text
GET /api/program-rules
```

- [ ] Render from backend structured JSON only.
- [ ] Show:
  - [ ] degree program
  - [ ] regulation/version
  - [ ] rule sections
  - [ ] rule descriptions
  - [ ] rule items
  - [ ] source labels
  - [ ] related issue codes, likely in a developer/details area
- [ ] Include the Softwareprojekt Wahlbereich caveat.
- [ ] Include the Wissenschaftliches Arbeiten Wahlbereich caveat.
- [ ] Do not parse `backend/knowledge_base/generated/degree_rules.md` in the frontend.
- [ ] Do not query Qdrant just to render rules.
- [ ] Do not duplicate backend validation logic in TypeScript.

## Phase 7: Study Plan Tab, Temporary Version

- [ ] Add `StudyPlanTab.tsx`.
- [ ] Initially render a clear empty state:

```text
No extracted study plan yet.
```

- [ ] If the latest chat response contains `rule_check_result`, show:
  - [ ] validation summary
  - [ ] LP totals
  - [ ] errors
  - [ ] warnings
- [ ] Make clear in code comments that this is temporary.
- [ ] Do not pretend that the full parsed module list is available if the backend does not expose it yet.

## Phase 8: Multilingual UI Foundation

- [ ] Add multilingual UI support with `next-intl`.
- [ ] Support at least English and German frontend chrome.
- [ ] Add locale message files for all user-visible frontend-owned strings.
- [ ] Add a language setting in Settings after the message catalogue exists.
- [ ] Persist the selected language in localStorage or the routing layer.
- [ ] Keep SettingsContext or a dedicated i18n provider as the frontend source of truth for the selected language.
- [ ] Do not translate backend-owned validation logic in the frontend.
- [ ] Render backend-provided answer text, citations, rule descriptions, and validation issue messages as returned by the API unless the backend exposes localized fields.
- [ ] If the Degree Rules tab needs fully localized rule text, add localized structured fields or a locale-aware response to `GET /api/program-rules` before translating those rules in the frontend.
- [ ] Update every locale file in the same change whenever adding or changing frontend UI text.

## Phase 9: Backend Endpoints Needed For Real Study Plan Tab

The current backend does not yet expose the parsed study plan as a stable resource. Add these before making the Study Plan tab fully useful:

```text
GET  /api/sessions/{session_id}/study-plan
PUT  /api/sessions/{session_id}/study-plan
POST /api/sessions/{session_id}/study-plan/check
```

- [ ] Add backend models for `StudyPlan` and `PlannedModule` API responses if needed.
- [ ] Add a session storage abstraction before relying on the tab for real data.
- [ ] Start with JSON-file storage if Postgres is intentionally deferred:

```text
backend/data/sessions/{session_id}.json
```

- [ ] Keep `MemorySaver` for LangGraph conversation state only during early development.
- [ ] Do not treat `MemorySaver` as production multi-user persistence.

## Phase 10: Study Plan Tab, Real Version

- [ ] Fetch:

```text
GET /api/sessions/{session_id}/study-plan
```

- [ ] Render:
  - [ ] specialization area
  - [ ] module table
  - [ ] module name
  - [ ] LP
  - [ ] area
  - [ ] Wahlbereich marker
  - [ ] ungraded marker
  - [ ] Bachelor-module marker
  - [ ] Wissenschaftliches Arbeiten marker
  - [ ] Softwareprojekt marker
  - [ ] LP totals
  - [ ] Wahlbereich LP
  - [ ] core and total Softwareprojekt counts
  - [ ] core and total Wissenschaftliches Arbeiten counts
  - [ ] validation errors/warnings
- [ ] Add manual editing only after the read-only overview works.
- [ ] When editing exists, save through:

```text
PUT /api/sessions/{session_id}/study-plan
```

- [ ] Re-check through:

```text
POST /api/sessions/{session_id}/study-plan/check
```

## Phase 11: Settings Tab

- [ ] Add `SettingsTab.tsx`.
- [ ] Include dark mode toggle.
- [ ] Include language selector after the multilingual UI foundation is implemented.
- [ ] Include developer section:
  - [ ] current session ID
  - [ ] API base URL
  - [ ] backend health status
  - [ ] button to refresh health
  - [ ] button to clear local chat/session
- [ ] Keep settings small in the first version.
- [ ] Do not add user accounts/auth in the first frontend pass.

## Phase 12: Docker Integration

- [ ] Add frontend Dockerfile if needed.
- [ ] Extend `fu_berlin_cs_consultant/docker-compose.yml`.
- [ ] Use ports:
  - [ ] backend: `5100`
  - [ ] frontend: `3000`
- [ ] Pass backend API URL into frontend container:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:5100
```

- [ ] Ensure the backend CORS settings allow the frontend dev origin.

## Phase 13: Verification

- [ ] Run frontend type check.
- [ ] Run frontend lint.
- [ ] Run frontend production build.
- [ ] Start backend.
- [ ] Start frontend.
- [ ] Manually verify:
  - [ ] Chat tab creates a session.
  - [ ] Chat tab receives an assistant response.
  - [ ] Degree Rules tab renders `GET /api/program-rules`.
  - [ ] Settings dark mode persists.
  - [ ] Settings language selection persists after multilingual support is implemented.
  - [ ] Settings backend health check works.
  - [ ] Study Plan tab empty state is honest before study-plan API exists.
- [ ] Later, add Playwright screenshot checks after the UI stabilizes.

## Open Decisions

- [ ] Should `next-intl` use locale-prefixed routes or a settings-only language switch for the first multilingual pass?
- [ ] Should the Study Plan tab remain read-only for the first complete milestone?
- [ ] Should JSON-file session storage be added before or after the first frontend shell?
- [ ] Should `GET /api/program-rules` include richer source citations per rule item?
- [ ] Should `GET /api/program-rules` eventually return localized rule text for English and German?

## Recommended First Milestone

- [ ] Scaffold frontend.
- [ ] Implement theme/settings.
- [ ] Implement app shell.
- [ ] Implement Chat tab against current backend.
- [ ] Implement Degree Rules tab against `GET /api/program-rules`.
- [ ] Implement Settings tab with dark mode and health check.
- [ ] Leave Study Plan tab as a truthful placeholder until the backend has explicit study-plan endpoints.
- [ ] Add multilingual UI support in the next milestone, after the first shell is usable.
