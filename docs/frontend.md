# Frontend Architecture

The static Next.js export is served at `/` (and `/consultant`) and uses React,
TypeScript, Material UI, and the App Router.

The browser-facing backend origin comes from `NEXT_PUBLIC_API_BASE_URL`. This
public value is embedded during `next build`, so rebuild and redeploy
`frontend/out` after changing it. The local Compose default is
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
  Session creation sends the degree; the Degree Rules tab fetches
  `GET /api/program-rules?degree=<id>`.
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
shown once per reset period when ten or fewer requests remain.

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

When the backend reports WizardFlow tracing as enabled
(`GET /api/usage` -> `diagnostic_tracing_enabled`), the developer section also
shows a `New Trace File` button. It calls `POST /api/tracing/reinit`, which
rotates the backend's WizardFlow trace to a fresh timestamped file (keeping the
graph and output configuration) and reports the new trace path. A disabled
tracer returns HTTP 409 with `error_code == "tracing_disabled"`.
