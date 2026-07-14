# Deployment (Docker / Compose / Caddy)

`docker-compose.yml` starts the backend locally. The optional static-frontend
preview uses the `frontend-preview` profile:

```text
frontend preview -> http://localhost:3000/
backend          -> http://localhost:8000
```

The optional `production` profile also starts Caddy on ports 80/443. Caddy
terminates HTTPS, serves `frontend/out` directly from `/srv`, and proxies only
backend traffic over the internal Compose network. Production therefore runs no
Node.js frontend container. Its certificate state persists in the `caddy_data`
volume.

## Two Caddyfiles, distinct roles

- Root `Caddyfile` belongs to the production `caddy` service: TLS, the `www`
  redirect, backend proxying, and the static export.
- `frontend/Caddyfile.preview` belongs only to the optional `frontend-preview`
  service; it is a minimal local static-file server and is **not** used in the
  production request path.

## Static frontend export

The frontend is a static Next.js export (`output: "export"`). Build it on the
local machine with `npm run build`; the generated `frontend/out/` directory is a
tracked deployment artifact and must be refreshed before deployment. The
browser-facing API base URL is baked into that export; the optional Docker
preview image packages the export unchanged:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_DEV_TOOLS=false
```

`NEXT_PUBLIC_API_BASE_URL` is intentionally host-facing because the JavaScript
runs in the user's browser, not inside the Docker network.

## Environment

Compose uses `.env` as the backend env file. Keep `.env.example` aligned when
adding required runtime variables.

Compose publishes application ports on `COMPOSE_BIND_ADDRESS` and reads
`FRONTEND_PORT` (preview only), `CONSULTANT_PORT`, `CORS_ALLOWED_ORIGINS`, and
`FORWARDED_ALLOW_IPS` from `.env`. Keep the application bind address on loopback
when the production Caddy profile is enabled. Production additionally requires
`APP_DOMAIN`, a static export built with the matching `NEXT_PUBLIC_API_BASE_URL`,
and matching CORS configuration.

## Build notes

The backend Dockerfile intentionally wraps apt update/install in timeouts. If
apt times out, investigate Docker network access to Debian mirrors before
changing Python dependencies.

For production, first rebuild `frontend/out/` locally and deploy the updated
repository revision, then run the production Compose profile; only `backend` and
Caddy run. Use `docker compose logs -f backend caddy` when production runtime
behavior is unclear.
