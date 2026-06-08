# NovaGhost — Visual Analyzer

Desktop screen-analysis tool with an authentication backend. Triple-tap a region, get an AI response as an on-screen overlay. Ships with a credit/role system, HWID device binding, and an admin portal.

---

## Architecture

```
novaghost/
├── main.py              ← Desktop client entry point (Python / CustomTkinter)
├── main.spec            ← PyInstaller build spec → dist/PortalClient.exe
├── config.py            ← Central config dataclass (env + disk settings)
├── core/                ← Boot sequence, single-instance guard, safe mode
├── ui/                  ← Login, dashboard, settings, admin portal views
├── engine/              ← Triple-tap detector, screen capture, overlay, hider
├── network/             ← Auth client, vision API client, update checker
├── services/            ← Credit, status, diagnostics, env management
├── helpers/             ← Crypto, validation, formatting, caching
├── utils/               ← Logging, hotkeys, alerts
└── server/
    ├── server.vps.js    ← Node.js Express auth server (VPS deployment)
    ├── schema.sql       ← SQLite schema — applied automatically on first start
    └── package.json     ← Node dependencies
```

**Backend:** Node.js Express + SQLite, deployed on a VPS at `novaghost.twistark.cloud`
**Client:** Python desktop app compiled to `PortalClient.exe`

---

## Requirements

### Desktop client
- Python 3.10+
- Windows (primary — `pywin32`, `winotify` are Windows-only)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) **or** [Ollama](https://ollama.com) installed locally (no key needed)

### Server (VPS)
- Node.js 20+
- PM2 (`npm install -g pm2`)
- Nginx + Certbot for HTTPS

---

## Quick Start (development)

```bash
# 1. Create and activate virtualenv
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env   # fill in GEMINI_API_KEY and AUTH_SERVER_URL

# 4. Launch desktop client
python main.py
```

---

## Build Client Exe

```powershell
.\venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller main.spec --noconfirm
# Output: dist\PortalClient.exe
```

---

## Configuration

### `.env` variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (`AIzaSy...` format from AI Studio) |
| `OPENROUTER_API_KEY` | — | OpenRouter key (optional fallback provider) |
| `OPENAI_API_KEY` | — | OpenAI key (optional) |
| `AUTH_SERVER_URL` | — | Auth backend URL (`https://novaghost.twistark.cloud`) |
| `TRIPLE_TAP_WINDOW` | `0.5` | Seconds to detect triple-tap gesture |
| `RESPONSE_DURATION` | `2.0` | Seconds the overlay stays visible |
| `GLOBAL_SHORTCUT` | `Ctrl+Shift+S` | Dashboard toggle hotkey |
| `HIDE_CONSOLE` | `true` | Hide console window on startup |
| `HIDE_PROCESS` | `true` | Hide from Alt+Tab / task manager |
| `DISABLE_CAPTURE_PROTECTION` | `false` | Allow screen capture of overlay |
| `DEBUG_MODE` | `false` | Verbose logging |

### Per-user settings (saved to `~/.novaghost/settings.json`)

- Active vision provider and model
- Fallback provider and model
- API keys (stored locally, never sent to backend)
- Ollama base URL (default `http://localhost:11434`)
- Crop box (screen region)
- Triple-tap window, response duration, global shortcut
- Answer text size (font pt), max characters on display

---

## Vision Providers

| Provider | Key required | Notes |
|----------|-------------|-------|
| `gemini` | `GEMINI_API_KEY` | Free tier: `gemini-2.5-flash-lite`, `gemini-3.5-flash` |
| `openrouter` | `OPENROUTER_API_KEY` | `google/gemini-2.5-flash` and others |
| `openai` | `OPENAI_API_KEY` | Any vision-capable model |
| `ollama` | **None** | Local inference — no cost, no internet |

> **Gemini note:** `gemini-2.0-flash` and `gemini-1.5-flash` are removed or require billing on v1beta. Use `gemini-2.5-flash-lite` (primary) + `gemini-3.5-flash` (fallback) on the free tier.

Configure in the **Settings** view. Primary + fallback both supported.

### Ollama (local, offline)

No API key needed. Runs entirely on your machine.

**Setup:**
1. Install Ollama from [ollama.com](https://ollama.com)
2. In Settings → set Active Provider to `ollama`
3. Click **Load** on the Ollama Model row — dropdown populates with installed models
4. To install a new model: type its name in the Install field (e.g. `moondream`) → click **Install**

**Recommended vision models:**

| Model | Size | Notes |
|-------|------|-------|
| `moondream` | ~1.7 GB | Fastest, good for MCQ screenshots |
| `llava` | ~4.1 GB | Better accuracy |
| `llava-phi3` | ~2.9 GB | Good balance |
| `minicpm-v` | ~5.5 GB | Best for dense text/documents |

**Auto-install:** If a model isn't installed when you triple-tap, the download starts automatically in the background. The overlay shows `"Installing moondream... — triple-tap again when ready"`. No manual step needed.

---

## How It Works

1. **Start engine** — click "Start Scanning Engine" on the Dashboard
2. **Window hides** — app withdraws to system tray
3. **Triple-tap** — click the mouse 3× within `TRIPLE_TAP_WINDOW` seconds
4. **Capture** — selected screen region is grabbed as PNG
5. **AI query** — image sent to configured provider (Gemini / OpenAI / OpenRouter / Ollama)
6. **Overlay** — response appears at top-left of screen for `RESPONSE_DURATION` seconds
7. **5-second cooldown** — enforced between requests to respect rate limits

---

## Database Schema

Five tables in SQLite (`novaghost.db` on VPS):

| Table | Purpose |
|-------|---------|
| `users` | Credentials, role, HWID binding, credits |
| `login_history` | Per-login IP, HWID, status (SUCCESS / FAILED / BANNED / DEVICE_MISMATCH) |
| `audit_log` | All admin actions with actor, target, and details |
| `invite_keys` | Single-use `PORTAL-XXXXXXXX` registration keys |
| `system_config` | `latest_version`, `changelog`, `download_url`, `announcements` |

---

## API Reference

### Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ping` | Health check |
| GET | `/api/announcements` | System announcements |
| GET | `/api/changelog` | Release notes text |
| GET | `/api/update?version=X` | Update check |
| POST | `/api/login` | Authenticate — returns JWT |
| POST | `/api/register` | Register with invite key |

### User (Bearer token required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/user/credits` | Credit balance |
| POST | `/api/user/consume-credit` | Deduct one credit |

### Admin (admin or moderator role)

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/admin/invites` | List / generate invite keys |
| DELETE | `/api/admin/invites/<key>` | Revoke invite key |
| GET/POST | `/api/admin/users` | List / create users |
| DELETE | `/api/admin/users/<username>` | Delete user |
| POST | `/api/admin/reset-password` | Reset password |
| POST | `/api/admin/reset-hwid` | Clear device binding |
| POST | `/api/admin/ban` | Ban / unban user |
| GET/POST | `/api/admin/users/<username>/credits` | View / manage credits |
| POST | `/api/admin/version` | Update system config (admin only) |
| GET | `/api/admin/audit-logs` | Last 150 audit entries |
| GET | `/api/admin/login-history` | Last 150 login entries |

---

## Role Permissions

| Action | admin | moderator | user |
|--------|-------|-----------|------|
| Create user | ✓ | user role only | — |
| Delete user | ✓ | — | — |
| Ban / unban | ✓ | non-admin only | — |
| Reset password | ✓ | non-admin only | — |
| Reset HWID | ✓ | ✓ | — |
| Manage credits | ✓ | — | — |
| Update system config | ✓ | — | — |
| Generate invite keys | ✓ | ✓ | — |
| View audit / login logs | ✓ | ✓ | — |

Primary owner account (`PRIMARY_OWNER` env var) is immune to ban, delete, and password reset by others.

---

## Security Notes

- Passwords hashed with bcrypt (10 rounds).
- JWT signed with HMAC-SHA256, 24-hour expiry.
- HWID binding — first login locks account to that device.
- Clock rollback detection on client startup.
- Single-instance mutex prevents multiple concurrent clients.
- Overlay excluded from screen capture (`WDA_EXCLUDEFROMCAPTURE`).
- **Set `JWT_SECRET` in VPS `.env`** — the default fallback is public knowledge.

---

## Logs

All files written to `~/.novaghost/`:

| File | Contents |
|------|---------|
| `novaghost.log` | Runtime logs |
| `crash.log` | Crash reports with stack traces |
| `settings.json` | Persisted user preferences |
| `test.log` | Last diagnostics run output |

---

## Server Deployment

See `DEPLOY.md` for full VPS setup guide.
