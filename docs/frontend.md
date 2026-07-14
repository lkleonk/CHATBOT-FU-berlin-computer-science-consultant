# Frontend Architecture

The static Next.js export is served at `/` (and `/consultant`) and uses React,
TypeScript, Material UI, and the App Router. Keep all frontend edits inside
`fu_berlin_cs_consultant/frontend/`.

## Tabs

- `Chat`: session creation, message send, assistant response, citations, and
  plan-check result summary.
- `Study Plan`: student-specific extracted plan, modules, LP totals, Wahlbereich
  data, and validation issues. Needs dedicated study-plan API endpoints before
  it can be complete.
- `Degree Rules`: read-only rendering of `GET /api/program-rules`, plus a
  persistent external link to the Modulio degree-structure escape room.
- `Course Registry`: read-only, locally filterable rendering of the selected
  degree's `GET /api/course-offerings` projection. It lists only courses present
  in the local semester-offering data and does not consume the request allowance.
- `Settings`: dark mode, request allowance, production-visible reset
  conversation, plus optional developer diagnostics.

## Conventions

- Use MUI components and `sx` styling. Do not add Tailwind.
- Prefer theme tokens over hardcoded colors.
- Use icon buttons where an established icon exists.
- Keep the first screen as the actual consultant app, not a landing page.
- Keep `SettingsContext` / `UsageContext` / `DegreeContext` as the frontend
  sources of truth for dark mode, request allowance/retention, and degree choice
  respectively (see Client State below).
- Keep API calls in `frontend/src/services/api.ts` and shared TypeScript API
  contracts in `frontend/src/types/api.ts`.
- Do not put degree-rule validation logic in TypeScript. The frontend renders
  backend data and validation results.
- If i18n is added later, use `next-intl` and update all locale files together.

The browser-facing backend origin comes from `NEXT_PUBLIC_API_BASE_URL`. This
public value is embedded during `next build`, so rebuild and commit the tracked
`frontend/out` deployment artifact after changing it. The local Compose default is
`http://localhost:8000`; production should use the public HTTPS origin handled
by the reverse proxy.

The optional Compose `production` profile runs Caddy on ports 80/443. Caddy
serves the locally built `frontend/out` directory directly and proxies
backend/API-documentation paths on the same public origin; no Node.js frontend
container runs in production. `NEXT_PUBLIC_API_BASE_URL` and
`CORS_ALLOWED_ORIGINS` should both use `https://<APP_DOMAIN>`.

## Client State

- `SettingsContext` owns dark mode.
- `UsageContext` owns the current client-IP action allowance and runtime
  retention information returned by `GET /api/usage`.
- `DegreeContext` owns the chosen degree program. It fetches the available
  degrees from `GET /api/degrees` (with a built-in fallback list for display
  when the backend is unreachable) and persists the choice in `localStorage`.
  Session creation sends the degree; the Degree Rules and Course Registry tabs
  fetch `GET /api/program-rules?degree=<id>` and
  `GET /api/course-offerings?degree=<id>` respectively.
- The session ID and rendered chat are kept in `sessionStorage`.
- The welcome-dialog version is kept in `localStorage` so material disclosure
  changes can display the dialog again. The dialog also reopens when no degree
  choice is stored.

## Degree Choice And Switching

The welcome dialog opens with card-style toggle buttons for the degree
programs; `Start consultation` stays disabled until one is selected. After the
welcome, the header subtitle is a compact degree switcher (`Select`). Changing
it with an active session or chat opens `DegreeSwitchDialog`, which warns that
the chat, uploaded study plan, and validation results will be discarded and
offers `Download chat` plus a shortcut to the Study Plan tab to print the
module summary first (that shortcut cancels the switch). Confirming deletes
the backend session, clears local chat/study-plan state, and the next message
creates a session for the new degree. With nothing to lose, the switch happens
immediately without the dialog.

## Request Allowance

The header chip opens `RequestUsageDialog`. Chat and transcript responses update
the context from `X-RateLimit-*` headers with scope `user_action`; the global LLM
quota is intentionally not displayed as a user's allowance. A warning dialog is
shown once per reset period when between one and ten requests remain.

When the allowance is fully exhausted (`remaining <= 0`), `QuotaExhaustedDialog`
is shown once per reset period. It explains that chat and transcript checks are
paused until the reset time and offers a shortcut to the Course Registry tab.
The Chat tab's input and transcript upload are disabled while exhausted, and the
message field placeholder shows the reset time. The read-only Course Registry and
Degree Rules tabs stay usable throughout.

## Chat Export And Reset

`Download chat` creates a Markdown file entirely in the browser. It includes
rendered messages, citations, and rule-check summaries, but not uploaded PDFs or
their extracted raw text.

`Reset conversation` remains visible in production. Its confirmation dialog
offers a download first, then calls `DELETE /api/sessions/{session_id}` and
clears local chat and study-plan state.

## Welcome And Data Disclosure

The versioned welcome dialog collects the degree-program choice and states that
the service is unofficial, answers may be wrong, requests are limited, session
data expires, and transcript text is processed by the configured LLM. When the
backend reports WizardFlow tracing as enabled, the dialog explicitly warns that
unredacted diagnostic traces may be retained separately from in-memory session
state.

## Developer Tools

`NEXT_PUBLIC_ENABLE_DEV_TOOLS=false` hides the API base URL, raw session ID,
health diagnostics, dummy data, manual health refresh, and the trace-file
button. It is a build-time UI switch, not a security boundary. Dark mode,
request allowance, chat download, and reset conversation remain available.

The developer section includes a persistent `Use bundled dummy data` switch for
the Course Registry. When enabled, the tab uses the explicitly fictional
fixtures under `app/consultant/dummy_data/` instead of requesting the backend,
and displays a visible dummy-preview warning. It is intended for static frontend
preview only and must never be presented as FU Berlin catalogue data.

The developer-only Study Plan preview switch displays a six-module partial
extract from `ressources/Leistungsuebersicht_Max_Mustermann_Demo.pdf` for
M.Sc. Informatik. The fixture lives under `app/consultant/dummy_data/`, hides
the transcript-upload action, and deliberately suppresses rule-check output so
the partial demo is never mistaken for a complete transcript or validation.

When the backend reports WizardFlow tracing as enabled
(`GET /api/usage` -> `diagnostic_tracing_enabled`), the developer section also
shows a `New Trace File` button. It calls `POST /api/tracing/reinit`, which
rotates the backend's WizardFlow trace to a fresh timestamped file (keeping the
graph and output configuration) and reports the new trace path. A disabled
tracer returns HTTP 409 with `error_code == "tracing_disabled"`.
