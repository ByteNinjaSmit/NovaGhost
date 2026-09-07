# NovaGhost — Visual Analyzer (Local Edition)

Desktop screen-analysis tool. Triple-tap a screen region, get an AI response as an on-screen overlay.

**This is the local-only build.** No login, no signup, no accounts, no admin portal, and no cloud server. Nothing to deploy — you run it on your own computer and enter your API key in the **Preferences** tab. Your key is stored locally in `~/.novaghost/settings.json` and is only sent to the AI provider you choose.

---

## Architecture

```
novaghost/
├── main.py              ← App entry point (Python / CustomTkinter)
├── main.spec            ← PyInstaller build spec → dist/PortalClient.exe
├── config.py            ← Central config dataclass (env + disk settings)
├── core/                ← Boot sequence, single-instance guard, safe mode
├── ui/                  ← Dashboard, preferences, diagnostics, release notes
├── engine/              ← Triple-tap detector, screen capture, overlay, hider
├── network/             ← Vision API client (Gemini / OpenAI / OpenRouter / Ollama)
├── services/            ← Status, diagnostics, environment checks
├── helpers/             ← Crypto, validation, formatting, caching
└── utils/               ← Logging, hotkeys, alerts
```

Pure Python desktop app. Optionally compiled to `PortalClient.exe`.

---

## Requirements

- Python 3.10+
- Windows (primary — `pywin32`, `winotify` are Windows-only)
- An API key for one cloud provider (Gemini / OpenAI / OpenRouter) **or** [Ollama](https://ollama.com) installed locally (no key needed, runs offline)

---

## Quick Start

```bash
# 1. Create and activate virtualenv
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
python main.py
```

The app opens straight to the Dashboard — no sign-in. Then:

1. Go to **Preferences**.
2. Pick your **Active Vision Provider** and enter its **API Key** (Gemini key from [Google AI Studio](https://aistudio.google.com/app/apikey)).
3. Click **Save System Configuration**.
4. Back on the **Dashboard**, click **Start Scanning Engine**.

A `.env` file is optional — everything can be set inside the app. If present, `GEMINI_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` pre-fill the fields.

---

## Build Exe

```powershell
.\venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller main.spec --noconfirm
# Output: dist\PortalClient.exe
```

---

## Configuration

### `.env` variables (all optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (`AIzaSy...` from AI Studio) |
| `OPENROUTER_API_KEY` | — | OpenRouter key (optional fallback provider) |
| `OPENAI_API_KEY` | — | OpenAI key (optional) |
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
- API keys (stored locally on this machine)
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

Configure in **Preferences**. Primary + fallback both supported.

### Ollama (local, offline)

No API key needed. Runs entirely on your machine.

**Setup:**
1. Install Ollama from [ollama.com](https://ollama.com)
2. In Preferences → set Active Provider to `ollama`
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

Use the tray icon (or the global shortcut) to show/hide the dashboard and restart the engine.

---

## Security / Privacy Notes

- API keys are stored locally in `~/.novaghost/settings.json` and only sent to the AI provider you select. With Ollama, nothing leaves your machine.
- Single-instance mutex prevents multiple concurrent clients.
- Overlay excluded from screen capture (`WDA_EXCLUDEFROMCAPTURE`).
- Clock rollback / config integrity checks run at startup; failures drop the app into Safe Mode (Diagnostics only).

---

## Logs

All files written to `~/.novaghost/`:

| File | Contents |
|------|---------|
| `novaghost.log` | Runtime logs |
| `crash.log` | Crash reports with stack traces |
| `settings.json` | Persisted user preferences and API keys |
| `test.log` | Last diagnostics run output |
