# Frontend Backend TODO

This list tracks frontend work needed to stay aligned with the current FastAPI backend. The PRD baseline only described `POST /api/match`, but the app now also uses auth, chat sessions, CV upload, profile, RAG admin, PMF metrics, audit logs, and human handoff endpoints.

## Already Integrated

- `POST /api/auth/login`, `POST /api/auth/signup`, `POST /api/auth/google`
- `POST /api/match` for the 4-step wizard and Top 3 major report
- `POST /api/chat` for routed advisor/RAG/CRM responses
- Chat session list, message history, rename, delete, and download endpoints
- `POST /api/upload-cv` and CV signal reuse in wizard/chat context
- `GET /api/profile/{user_id}` and `POST /api/profile/{user_id}`
- `GET /api/metrics` for PMF/admin dashboards
- `GET /api/handoff-summary` for staff handoff context
- Admin audit, pending handoff, RAG status, RAG ingest, and RAG config endpoints

## Completed

- Replaced runtime hardcoded backend calls with `services/api.js` helpers or `VITE_API_URL`.
- Added a single `/api/chat` response normalizer in `services/api.js` for `answer`/`response`, `major`/`top3`, and `sources`/`references`.
- Added consistent 401/403 handling in the Axios interceptor for expired tokens and role-protected routes.
- Protected `/wizard` with an auth guard because `POST /api/match` requires a token.
- Moved RAG streaming ingest into a shared API helper that uses `VITE_API_URL` and the same auth-token logic.
- Added staff/admin-only display of backend `intent` and `status` metadata in chat messages.
- Added frontend chat fallback states for rate limits, judge rejection, missing profile, backend fallback, guardrail blocks, and model/network errors.

## P1 TODO

- Add form-level validation that mirrors backend validation for wizard answers, profile fields, CV upload size/type, and chat length.
- Add optimistic UI rollback for failed session rename/delete actions.

## P2 TODO

- Add integration tests for auth, wizard match, chat session history, CV upload, staff metrics, and admin RAG controls.
- Add a frontend contract fixture for `/api/match` and `/api/chat` so UI mapping can be tested without a live backend.
- Add user-facing empty states for no metrics, no audit logs, no pending handoffs, and empty RAG collections.
- Add staff/admin filters that match backend query params exactly: `hours`, `limit`, `offset`, `user_id`, and `only_fallback`.
- Add a visible disclaimer on recommendation cards when backend returns `fallback: true`.

## Known Contract Risks

- Static HTML mockups under `app/frontend/html/` still contain localhost examples; runtime React code uses `services/api.js`.
- `/api/profile/{user_id}/cv` is referenced by the frontend service but is not listed in the current backend route scan.
