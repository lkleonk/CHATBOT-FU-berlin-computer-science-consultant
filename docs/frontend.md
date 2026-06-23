# Frontend Architecture

The standalone Next.js frontend is served at `/consultant` and uses React,
TypeScript, Material UI, and the App Router.

## Client State

- `SettingsContext` owns dark mode.
- `UsageContext` owns the current client-IP action allowance and runtime
  retention information returned by `GET /api/usage`.
- The session ID and rendered chat are kept in `sessionStorage`.
- The welcome-dialog version is kept in `localStorage` so material disclosure
  changes can display the dialog again.

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

The versioned welcome dialog states that the service is unofficial, answers may
be wrong, requests are limited, session data expires, and transcript text is
processed by the configured LLM. When the backend reports WizardFlow tracing as
enabled, the dialog explicitly warns that unredacted diagnostic traces may be
retained separately from in-memory session state.

## Developer Tools

`NEXT_PUBLIC_ENABLE_DEV_TOOLS=false` hides the API base URL, raw session ID,
health diagnostics, dummy data, and manual health refresh. It is a build-time UI
switch, not a security boundary. Dark mode, request allowance, chat download,
and reset conversation remain available.
