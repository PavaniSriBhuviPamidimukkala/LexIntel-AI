# LexIntel-AI
Intelligent Legal Research &amp; Case Retrieval Platform

## Environment setup

Copy `.env.example` to `.env` for the PostgreSQL Compose service and
`backend/.env.example` to `backend/.env` for the API. Set a strong
`POSTGRES_PASSWORD` and use the same password in `DATABASE_URL`. When using
Gemini, set `GEMINI_API_KEY` to a valid key. Do not commit `.env` files.
PostgreSQL binds to loopback by default; production deployments should keep it
on a private network and avoid publishing its port publicly.

Production API deployments must set `ENVIRONMENT=production`,
`AUTH_MODE=proxy`, and `TRUSTED_PROXY_CIDRS` to the exact proxy IP address(es)
or private subnet(s). The API accepts `X-Auth-Request-Email` or
`X-Auth-Request-User` identity assertions only from those network ranges.
Configure the proxy (for example, self-hosted oauth2-proxy with an OIDC
identity provider) to authenticate users, strip any client-supplied
`X-Auth-Request-*` headers, and set its own verified identity header. Keep the
API unreachable except through that proxy; the IP allowlist is a trust
boundary, not a substitute for network isolation. Local development defaults
to `AUTH_MODE=disabled`.

Set `CORS_ALLOWED_ORIGINS` in `backend/.env` to the exact frontend origin(s)
used by the deployment. The default allows the local Vite development server.
The backend upload limit defaults to 25 MiB and can be adjusted with
`MAX_UPLOAD_SIZE_BYTES`.

Copy `frontend/.env.example` to `frontend/.env` for local development. Set
`VITE_API_URL` to the publicly reachable backend URL for a production build;
production URLs must use HTTPS. Values prefixed with `VITE_` are included in
the browser bundle and must never contain secrets.
