# NovaGhost — Visual Intelligence & Aptitude Analysis Engine (Local Edition)

High-performance desktop visual analysis and assessment preparation tool. Triple-tap a screen region to capture, analyze questions via visual AI and deterministic solvers, and receive instant on-screen answers formatted strictly for exam selection or value entry.

**This is the local-only build.** No login, no signup, no accounts, no admin portal, and no cloud telemetry. Nothing to deploy — run it directly on your machine and configure your API key in **Preferences**. Keys are stored locally in `~/.novaghost/settings.json` and only transmitted to your selected AI provider.

---

## Key Capabilities

- **Zero-Hallucination SymPy Math Engine**: Deterministic symbolic equation solver, arithmetic verification, and built-in aptitude formulas (percentages, profit/loss, simple/compound interest, time & work, average speed, permutations, combinations, and AP/GP/quadratic series).
- **OpenCV Visual Feature Extraction**: Contour analysis with `cv2.approxPolyDP` extracting polygon vertex counts, geometric shape classification, fill ratios, orientation angles, and horizontal/vertical symmetry scores for non-verbal reasoning.
- **136-Bit Perceptual Hashing & Zero-Latency Cache**: Composite `dHash` + `aHash` + luminance matching with Hamming distance $\le 3$ for sub-10ms lookup on repeated or slightly altered questions.
- **Multi-Question Detection & Tabbed Overlay**: Automatically splits multiple questions in a single screenshot into interactive tabs (`[Q1]`, `[Q2]`, ..., `[ALL]`), complete with mouse-wheel scrolling, one-click clipboard copying, and manual dismissal.
- **Strict Assessment Formats (A–G)**: Answers strictly output exact values, option letters, or positions (e.g., `2nd from LEFT / 3rd from RIGHT`, grid row/col) without conversational fluff or truncated decimals.
- **Window Display Affinity Protection**: Uses Win32 `SetWindowDisplayAffinity(hwnd, 0x11)` (`WDA_EXCLUDEFROMCAPTURE`) on the root OS window handle to ensure the overlay never captures itself in screenshot cycles.

---

## Architecture

```
novaghost/
├── main.py                     ← App entry point (Python / CustomTkinter)
├── main.spec                   ← PyInstaller build spec → dist/PortalClient.exe
├── config.py                   ← Central config dataclass (env + disk settings)
├── core/                       ← Boot sequence, single-instance guard, safe mode
├── ui/                         ← Dashboard, preferences, diagnostics, release notes
├── engine/                     ← Core analysis pipeline:
│   ├── capture.py              ← Screen capture & region selection
│   ├── detector.py             ← Triple-tap input gesture detector
│   ├── overlay.py              ← Dark overlay with scrolling, tabs, copy & WDA protection
│   ├── processor.py            ← Pipeline coordinator & multi-question dispatcher
│   ├── question_classifier.py  ← Universal question recognition engine
│   ├── screenshot_processor.py ← OpenCV & PIL enhancement, quality, layout detection
│   ├── visual_feature_extractor.py ← OpenCV geometric contour, vertex & symmetry analysis
│   ├── math_engine.py          ← Deterministic SymPy algebraic & aptitude solver
│   ├── perceptual_cache.py     ← 136-bit perceptual hash zero-latency cache (<10ms)
│   ├── schemas.py              ← Strict output formatting, multi-question & positions
│   ├── answer_validator.py     ← Multi-point answer validation & sanity checks
│   └── solvers/                ← Specialized domain solvers:
│       ├── numerical_solver.py           ← Quantitative aptitude & math verifier
│       ├── data_interpretation_solver.py ← Bar, pie, line, table extraction
│       ├── figure_series_solver.py       ← 8-image to 9th figure series solver
│       ├── figure_matrix_solver.py       ← 2x2 & 3x3 matrix solvers
│       ├── visual_reasoning_solver.py    ← Mirror, water, paper folding, embedded
│       ├── logical_reasoning_solver.py   ← Blood relations, direction, syllogisms
│       ├── verbal_reasoning_solver.py    ← Reading comp, synonyms, grammar
│       └── technical_mcq_solver.py       ← DBMS, OS, networks, technical MCQs
├── network/                    ← Vision API client & prompt engine:
│   ├── api_client.py           ← Multi-provider client (Gemini/OpenAI/OpenRouter/Ollama)
│   └── prompt_engine.py        ← Structured prompt generator with JSON contracts
├── services/                   ← Status, diagnostics, environment checks
├── helpers/                    ← Crypto, validation, formatting, caching
├── utils/                      ← Logging, hotkeys, alerts
└── tests/                      ← Comprehensive test & synthetic evaluation suite:
    ├── test_schemas.py
    ├── test_classifier.py
    ├── test_solvers.py
    ├── test_screenshot_processor.py
    ├── test_api_client.py
    ├── test_math_engine.py
    ├── test_multi_question.py
    ├── test_perceptual_cache.py
    ├── test_visual_feature_extractor.py
    └── test_synthetic_dataset.py
```

Pure Python desktop app. Optionally compiled to a standalone Windows executable `PortalClient.exe`.

---

## Standardized Answer Formats

NovaGhost automatically categorizes questions and formats responses into one of seven strict formats:

| Format | Category | Output Structure |
|---|---|---|
| **Format A** | Labeled Image Options | `CORRECT ANSWER: OPTION <N>`<br>`Position: <X> from LEFT`<br>`Position: <Y> from RIGHT`<br>`Full answer: Option <N> – <Description>` |
| **Format B** | Unlabeled Image Options | `CORRECT ANSWER: <Position>`<br>`Equivalent: <Alt Position>`<br>`Option: <Visual Description>` |
| **Format C** | Standard Text MCQ | `CORRECT OPTION: <Letter>`<br>`FULL ANSWER: <Text>` |
| **Format D** | Numerical Answer Type (NAT) | `ENTER THIS VALUE:`<br>`# <Value>`<br>`Complete numerical answer: <Value>` |
| **Format E** | Multiple Select (MSQ) | `CORRECT OPTIONS: <A, B, ...>`<br>`SELECT: <A and B>` |
| **Format F** | Data Interpretation (DI) | `CORRECT OPTION: <Letter>`<br>`FULL ANSWER: <Value/Text>` |
| **Format G** | Low Resolution / Unclear | `UNCLEAR SCREENSHOT: <Details>` |

---

## Requirements

- Python 3.10+
- Windows 10/11 (primary — `pywin32`, `winotify` are Windows-native)
- An API key for a cloud vision provider (Gemini / OpenAI / OpenRouter) **or** [Ollama](https://ollama.com) installed locally (free, fully offline)

---

## Quick Start

```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
python main.py
```

The application opens directly to the Dashboard:
1. Navigate to **Preferences**.
2. Select your **Active Vision Provider** and paste your **API Key** (e.g. Gemini key from [Google AI Studio](https://aistudio.google.com/app/apikey)).
3. Click **Save System Configuration**.
4. Return to the **Dashboard** and click **Start Scanning Engine**.

---

## Automated Test Suite

To run all 57 unit tests, solver validations, and synthetic benchmarks:

```powershell
python -m unittest discover tests -v
```

**Verification Results:**
- **57/57 tests passing** (100% accuracy, 0 failures, 0 errors).
- Evaluates:
  - SymPy equation solving, percentage relationships, interest, time & work, series extrapolation
  - Multi-question parsing and tabbed formatting
  - 136-bit perceptual caching and near-match thresholding
  - OpenCV polygon approximation, vertex classification, and symmetry scoring
  - Layout detection, image contrast boosting, and low-resolution heuristics
  - Synthetic 25-question cross-category test suite

---

## Building Executable

To compile into a standalone Windows binary:

```powershell
.\venv\Scripts\Activate.ps1
pip install pyinstaller
pyinstaller main.spec --noconfirm
# Generated executable located at: dist\PortalClient.exe
```

---

## Configuration

### Environment Variables (`.env`, all optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (`AIzaSy...`) |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `TRIPLE_TAP_WINDOW` | `0.5` | Seconds allowed to trigger a triple-click gesture |
| `RESPONSE_DURATION` | `2.0` | Seconds before auto-fade (manual dismiss / `Esc` also supported) |
| `GLOBAL_SHORTCUT` | `Ctrl+Shift+S` | Hotkey to toggle dashboard visibility |
| `HIDE_CONSOLE` | `true` | Hide console window on launch |
| `HIDE_PROCESS` | `true` | Suppress window from Alt+Tab / Task Manager listing |
| `DISABLE_CAPTURE_PROTECTION` | `false` | Disable `WDA_EXCLUDEFROMCAPTURE` |
| `DEBUG_MODE` | `false` | Enable verbose debug logging |

### User Settings (`~/.novaghost/settings.json`)

All settings can be configured directly in the **Preferences** tab:
- Active & fallback vision providers and model names
- Provider API keys (stored locally)
- Ollama base URL (default: `http://localhost:11434`)
- Crop box coordinates and dimensions
- Gesture timings and overlay duration
- Display font size and character ceilings

---

## Vision Providers

| Provider | Key Required | Models / Notes |
|----------|-------------|----------------|
| `gemini` | `GEMINI_API_KEY` | `gemini-2.5-flash-lite`, `gemini-3.5-flash` |
| `openrouter` | `OPENROUTER_API_KEY` | `google/gemini-2.5-flash`, Anthropic, etc. |
| `openai` | `OPENAI_API_KEY` | `gpt-4o`, `gpt-4o-mini` |
| `ollama` | **None** | Completely offline inference via local models |

### Ollama Setup (Offline)

1. Download and install Ollama from [ollama.com](https://ollama.com).
2. In Preferences, set Active Provider to `ollama`.
3. Click **Load** to discover installed vision models (e.g. `moondream`, `llava`, `minicpm-v`).
4. To install a new model, enter its name in the Install field and click **Install**.
5. *Auto-install feature*: If a model is not installed upon gesture trigger, background download starts automatically while alerting the user.

---

## Operational Flow

1. **Start Engine**: Click "Start Scanning Engine" on Dashboard.
2. **Gesture Trigger**: Triple-tap mouse button within `TRIPLE_TAP_WINDOW` seconds.
3. **Capture & Pre-process**: Screen region is captured; OpenCV evaluates blur, boosts contrast, and checks the 136-bit perceptual cache.
4. **Cache Check**: If an identical or near-identical image ($\le 3$ Hamming distance) exists, cached answer returns in $<10\text{ ms}$.
5. **Visual Feature Extraction**: OpenCV extracts contours, vertex count, and symmetry scores.
6. **AI Analysis & Solver Execution**: Vision model analyzes visual elements; SymPy math engine verifies and corrects numerical formulas.
7. **Overlay Display**: Displays formatted answer (or multi-question tabs) protected from capture via `SetWindowDisplayAffinity(0x11)`.
8. **Cooldown**: Built-in 5-second cooldown protects API rate limits.

---

## Security & Privacy

- **Local Storage Only**: API keys and configurations reside strictly on your local disk in `~/.novaghost/settings.json`.
- **Zero Cloud Infrastructure**: No user management, no telemetry, no remote databases.
- **Window Display Affinity**: Root window handle (`GA_ROOT`) is registered with `WDA_EXCLUDEFROMCAPTURE` to eliminate recursive screenshot capture.
- **Single-Instance Mutex**: Guards against duplicate background processes.
- **Startup Integrity Checks**: Detects clock rollback and configuration tampering, entering Safe Mode if anomalies are found.

---

## Logs & Diagnostics

All runtime artifacts are stored under `~/.novaghost/`:
- `novaghost.log`: Real-time application logs
- `crash.log`: Unhandled exceptions and stack traces
- `settings.json`: Persisted local configurations
- `test.log`: Diagnostic run output
