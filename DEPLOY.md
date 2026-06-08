# Deployment Guide — NovaGhost

Two deployment paths: **local Flask server** (dev / self-hosted) and **Cloudflare Workers** (production).

---

## Option A — Local Flask Server

### 1. Install dependencies

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux

pip install flask bcrypt
```

### 2. Set environment variables

```bash
copy .env.example .env
```

Minimum required values in `.env`:

```env
JWT_SECRET=<random 64-char string>
INIT_SECRET=<random string>
PRIMARY_OWNER=admin
AUTH_SERVER_URL=http://127.0.0.1:5000
```

### 3. Initialize the database

```bash
python server/db.py
```

Creates `server/auth.db` and seeds the `admin` account (`admin` / `admin123`).
**Change the admin password immediately after first login.**

### 4. Start the server

```bash
python server/app.py
```

Server listens on `http://127.0.0.1:5000` by default. Bind to `0.0.0.0` and set a reverse proxy (nginx, Caddy) for LAN/internet exposure.

### 5. Point the desktop client

In `.env`:

```env
AUTH_SERVER_URL=http://127.0.0.1:5000
```

Or set it in the client's Settings view.

### Production hardening (self-hosted)

- Run behind a reverse proxy with TLS (Let's Encrypt / Caddy).
- Set `debug=False` in `app.py` (already off by default via env).
- Restrict `host` to `127.0.0.1` when proxied locally.
- Rotate `JWT_SECRET` to invalidate all existing sessions.
- Back up `server/auth.db` regularly — it is excluded from git intentionally.

---

## Option B — Cloudflare Workers + D1 (Production)

### Prerequisites

- Cloudflare account with Workers and D1 access.
- Node.js 18+ installed.
- Wrangler CLI:

```bash
npm install -g wrangler
wrangler login
```

### 1. Create the D1 database

```bash
wrangler d1 create portal-db
```

Copy the returned `database_id` into `server/wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "portal-db"
database_id = "<your-database-id>"
```

### 2. Apply the schema

```bash
# Remote (production D1)
wrangler d1 execute portal-db --remote --file=server/schema.sql

# Local preview (optional)
wrangler d1 execute portal-db --local --file=server/schema.sql
```

This creates all tables and seeds `system_config` with default values.
The first user to register via `POST /api/register` becomes the admin automatically.

### 3. Set Worker secrets

Set each secret via Wrangler (never commit these to source):

```bash
wrangler secret put JWT_SECRET
# paste your secret when prompted

wrangler secret put INIT_SECRET
# paste your secret when prompted

wrangler secret put PRIMARY_OWNER
# type: admin  (or your chosen owner username)
```

These are injected into `env` at runtime in `worker.js`.

### 4. Install Node dependencies

```bash
cd server
npm install
```

### 5. Deploy

```bash
cd server
wrangler deploy
```

Wrangler prints the deployment URL, e.g.:
```
https://novaghost-auth.<your-subdomain>.workers.dev
```

### 6. Point the desktop client

In `.env`:

```env
AUTH_SERVER_URL=https://novaghost-auth.<your-subdomain>.workers.dev
```

### 7. Verify

```bash
curl https://novaghost-auth.<your-subdomain>.workers.dev/api/ping
# {"status":"online","database":"connected","timestamp":"..."}
```

---

## Cloudflare Workers — Local Preview

Test locally before deploying:

```bash
cd server
wrangler dev
```

Uses a local D1 instance. Set `AUTH_SERVER_URL=http://127.0.0.1:8787` in `.env` while previewing.

---

## Database Management

### Export D1 data (backup)

```bash
wrangler d1 export portal-db --remote --output=backup.sql
```

### Run ad-hoc queries

```bash
wrangler d1 execute portal-db --remote --command="SELECT * FROM users"
```

### Reset / re-apply schema (destructive)

```bash
wrangler d1 execute portal-db --remote --file=server/schema.sql
```

`schema.sql` uses `DROP TABLE IF EXISTS` — this wipes all data. Only run on a fresh deployment or intentional reset.

---

## Bootstrap Admin Registration

If the database is empty (fresh deployment), the **first** `POST /api/register` call automatically receives the `admin` role — no invite key needed.

To create additional admins after bootstrap, use the `X-Init-Secret` header:

```bash
curl -X POST https://<worker>/api/register \
  -H "Content-Type: application/json" \
  -H "X-Init-Secret: <your INIT_SECRET>" \
  -d '{"username":"newadmin","password":"secret","role":"admin"}'
```

---

## Environment Variable Reference

| Variable | Local Flask | Cloudflare | Required | Description |
|----------|------------|------------|----------|-------------|
| `JWT_SECRET` | `.env` | `wrangler secret` | **Yes (prod)** | JWT signing key |
| `INIT_SECRET` | `.env` | `wrangler secret` | Recommended | Bootstrap registration header |
| `PRIMARY_OWNER` | `.env` | `wrangler secret` | Optional | Protected owner username |
| `AUTH_SERVER_URL` | `.env` (client) | n/a | Yes | Backend URL used by client |

---

## Switching from Local to Cloud

1. Deploy Worker and apply schema (steps above).
2. Update `AUTH_SERVER_URL` in `.env` on each client machine.
3. Re-register users — the D1 database starts empty.
4. Existing `server/auth.db` is not migrated automatically.

To migrate local SQLite to D1:

```bash
# Export local data
sqlite3 server/auth.db .dump > local_dump.sql

# Manually convert INSERT statements as needed, then:
wrangler d1 execute portal-db --remote --file=local_dump.sql
```

---

## Worker Configuration (`server/wrangler.toml`)

```toml
name = "novaghost-auth"            # Worker name (appears in dashboard URL)
main = "worker.js"                 # Entry point
compatibility_date = "2024-01-01"  # Runtime compatibility

[[d1_databases]]
binding = "DB"                     # env.DB in worker.js
database_name = "portal-db"        # D1 database name
database_id = "..."                # from: wrangler d1 create portal-db
```

To rename the Worker subdomain, change `name` and redeploy.
