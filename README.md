# OSM Multilingual Name Editor

OSM Multilingual Name Editor is a tool aimed at facilitating multilingual mapping at
[OpenStreetMap](https://www.openstreetmap.org). Hence it's a small attempt at helping
to preserve the world's rich cultural and linguistic heritage.

Point it this editor at an administrative area (by relation ID), fetch streets / POIs / 
relations or basically anything bearing a `name` tag, edit `name` + `name:<lang>` 
columns in a table, see selected objects on a map, and upload the result back to OSM 
as a changeset.

Backend: Python (FastAPI). 
Frontend: Vue 3 + TypeScript (Vite) + Leaflet. 



## Installation

The following instructions are meant for deployment on your local machine. If you want 
to deploy it on a production-grade server, it is assumed you already know what to do.

For local installation, the easiest way is to run it in Docker behind a Caddy proxy 
that terminates HTTPS at `https://localhost`. An OSM's OAuth2 application is required
to have an HTTPS callback URI


### Prerequisites

- Docker + Docker Compose
- `openssl` (for the one-time local cert generation)

## 1. Generate a local HTTPS cert

```bash
./proxy/generate-cert.sh
```

This creates a self-signed cert for `localhost` under `proxy/certs/` (gitignored —
it's a private key, regenerate it per checkout rather than sharing it). It's not
trusted by your OS/browser by default, though.

## 2. Backend config

```bash
cd backend
cp config.example.yaml config.yaml
cd ..
```

Edit `backend/config.yaml`:
- Set a random `session_secret` (e.g. `openssl rand -hex 32`).
- Leave `environment: dev` for now — you'll fill in OAuth credentials below.

## 3. Start everything

```bash
docker compose up --build
```

This starts three containers:
- `backend` — FastAPI, auto-reloading on code changes, also published directly on
  `http://localhost:8000` for debugging (e.g. curl).
- `frontend` — Vite dev server with hot reload, also published directly on
  `http://localhost:5173` for debugging.
- `proxy` — Caddy, terminating HTTPS on `https://localhost` (port 443), routing
  `/api/*` to the backend and everything else to the frontend. **This is the URL to
  actually use the app at** — frontend and backend are same-origin behind it, which
  is also what makes OAuth login work.

Open **https://localhost**.

Smoke-test the backend directly without going through the browser:

```bash
curl -X POST localhost:8000/api/fetch \
  -H "Content-Type: application/json" \
  -d '{"admin_id": 1155954, "object_types": ["streets","named"], "languages": ["de"]}'
```

(`1155954` is Planken, Liechtenstein's smallest municipality — a good tiny test case.)

## 4. Registering an OSM OAuth2 application (required for login/upload)

Only you can do this part — it requires an OSM account and can't be automated.

**Dev/sandbox server (recommended for testing first):**

1. Create an account (separate from your main OSM account!) at
   https://master.apis.dev.openstreetmap.org
2. Go to https://master.apis.dev.openstreetmap.org/oauth2/applications and register
   a new application:
   - Redirect URI: `https://localhost/api/auth/callback`
   - Confidential client, Authorization Code grant
   - Scopes: `read_prefs write_api`
3. Copy the generated Client ID / Client Secret into `backend/config.yaml` under
   `environments.dev.client_id` / `client_secret`.

**Production** (only once you're confident — this edits real map data):

1. Go to https://www.openstreetmap.org/oauth2/applications on your normal OSM account
   and register an application the same way, redirect URI/scopes as above.
2. Fill in `environments.prod.client_id` / `client_secret`.
3. Set `environment: prod` in `config.yaml` when you want to switch.

Restart the backend container after editing `config.yaml`
(`docker compose restart backend`).

## Important limitation: Overpass only has production data

The **prod/dev toggle only affects where you log in and upload changesets** — object
*fetching* always queries the public Overpass API, which only mirrors real production
OSM data (there's no Overpass mirror for the dev/sandbox server). So with
`environment: dev`, you'll fetch real objects but the dev server generally won't have
matching IDs to upload against — uploads there will mostly fail unless you've created
matching test data on the dev server yourself. Use `dev` to verify the OAuth
login flow works; use `prod` (carefully!) to actually verify uploads end-to-end.

## Other notes

- Uploading replaces an element's entire tag set with what was fetched + your edits.
  If someone else changed unrelated tags on that element between your fetch and your
  upload, those changes are overwritten. Fine for a focused name-editing tool, but
  worth knowing.
- POI tag scope is configurable via `poi_tags` in `config.yaml`.
- `docker compose down` stops everything; add `-v` to also drop the frontend
  `node_modules` volume if you want a totally clean reinstall.
