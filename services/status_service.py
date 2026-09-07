import logging
from typing import Dict

from config import config

logger = logging.getLogger("StatusService")

HEALTH_DISPLAY_LABELS: Dict[str, str] = {
    "internet":      "Internet",
    "visual_system": "Visual System",
    "ai_engine":     "AI Engine",
    "storage":       "Storage",
}

def check_all() -> Dict[str, str]:
    status = {key: "red" for key in HEALTH_DISPLAY_LABELS}

    try:
        import requests
        res = requests.get("https://1.1.1.1", timeout=3)
        status["internet"] = "green" if res.status_code == 200 else "yellow"
    except Exception:
        status["internet"] = "red"

    # Visual system is nominal if capture is functional
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        if screenshot and screenshot.size[0] > 0:
            status["visual_system"] = "green"
        else:
            status["visual_system"] = "yellow"
    except Exception:
        status["visual_system"] = "red"

    # AI engine is ready once an API key is configured for the active provider.
    # Ollama runs locally, so it does not need internet.
    if config.has_primary_key():
        if config.ACTIVE_PROVIDER == "ollama" or status["internet"] == "green":
            status["ai_engine"] = "green"
        else:
            status["ai_engine"] = "yellow"
    else:
        status["ai_engine"] = "yellow"

    try:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        test_file = config.LOG_DIR / ".status_write_test"
        test_file.write_text("ok")
        test_file.unlink()
        status["storage"] = "green"
    except Exception:
        status["storage"] = "red"

    return status
