# LexIntel-AI
Intelligent Legal Research &amp; Case Retrieval Platform

## Environment setup

Copy `.env.example` to `.env` for the PostgreSQL Compose service and
`backend/.env.example` to `backend/.env` for the API. Set a strong
`POSTGRES_PASSWORD` and use the same password in `DATABASE_URL`. When using
Gemini, set `GEMINI_API_KEY` to a valid key. Do not commit `.env` files.
PostgreSQL binds to loopback by default; production deployments should keep it
on a private network and avoid publishing its port publicly.

Set `AUTH_MODE=jwt` and `JWT_SECRET_KEY` to a randomly generated secret of at
least 32 bytes to enable built-in registration and JWT login. The example
configuration contains a placeholder that must be replaced. Set
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES` to adjust token lifetime. `AUTH_MODE=proxy`
continues to support trusted authentication proxies; `AUTH_MODE=disabled` is
for local development only. The built-in React login requires `AUTH_MODE=jwt`;
proxy mode is for deployments that provide an external proxy-managed login
flow. Production API deployments must set
`ENVIRONMENT=production` and use either JWT or proxy authentication. For proxy
mode, set `TRUSTED_PROXY_CIDRS` to the exact proxy IP address(es) or private
subnet(s). The API accepts `X-Auth-Request-Email` or
`X-Auth-Request-User` identity assertions only from those network ranges.
Configure the proxy (for example, self-hosted oauth2-proxy with an OIDC
identity provider) to authenticate users, strip any client-supplied
`X-Auth-Request-*` headers, and set its own verified identity header. Keep the
API unreachable except through that proxy; the IP allowlist is a trust
boundary, not a substitute for network isolation.
Tenant data endpoints reject anonymous requests when `AUTH_MODE=disabled`;
use JWT or a trusted proxy identity that maps to an existing account.

For a new database, create all application tables with
`cd backend && python -m app.db.init_db`. For an existing database, back up the
database and apply the tenant-isolation migration with
`cd backend && alembic upgrade head`. The migration adds a nullable
`legal_documents.user_id` foreign key so existing documents without a known
owner remain inaccessible rather than being assigned to an arbitrary user.
New API-created and uploaded documents always receive the authenticated
owner's ID. Registration and login are available at `/auth/register` and
`/auth/login`; the `/documents`, `/ask`, `/metrics`, and `/history` APIs require
a user-specific authenticated identity. In proxy mode, the trusted proxy
identity must match an existing account.

Set `CORS_ALLOWED_ORIGINS` in `backend/.env` to the exact frontend origin(s)
used by the deployment. The default allows the local Vite development server.
The backend upload limit defaults to 25 MiB and can be adjusted with
`MAX_UPLOAD_SIZE_BYTES`. Documents, retrieval, chat history, and dashboard
metrics are scoped to the authenticated user; legacy documents with no owner
are excluded from every user-facing query.

Copy `frontend/.env.example` to `frontend/.env` for local development. Set
`VITE_API_URL` to the publicly reachable backend URL for a production build;
production URLs must use HTTPS. Values prefixed with `VITE_` are included in
the browser bundle and must never contain secrets.

## Frontend pages

The React app provides `/login`, a dashboard at `/`, document upload at
`/upload`, document history at `/documents`, legal question answering at
`/ask`, and Evaluation Metrics at `/evaluation-metrics`. Protected pages use
the configured backend authentication mode. The dashboard reads document
counts from the existing documents API. Evaluation Metrics reads document and
chunk counts, query statistics, timings, and service health from `/metrics/`.
Chat history is persisted per user and available from `/history/`; aggregate
metrics and timing histories are calculated only from that user's records.
Individual query text is not returned by the metrics endpoint.
The dashboard's Accessibility link opens `/evaluation-metrics/accessibility`,
which summarizes implementation checks and recommended follow-up testing. Its
calculated score is an implementation checklist estimate, not a certified
WCAG audit.
