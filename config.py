import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

logger = logging.getLogger("Config")

@dataclass
class Config:
    CURRENT_VERSION: str = "3.0.0"

    # Active visual provider and model settings
    ACTIVE_PROVIDER: str = "gemini"
    ACTIVE_MODEL: str = "gemini-2.5-flash-lite"
    
    # Provider keys (ollama uses "local" sentinel — no real key needed)
    API_KEYS: dict = field(default_factory=lambda: {
        "gemini": os.getenv("GEMINI_API_KEY", ""),
        "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "ollama": "local"
    })

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Fallback configuration
    FALLBACK_ENABLED: bool = True
    FALLBACK_PROVIDER: str = "openrouter"
    FALLBACK_MODEL: str = "gemini-3.5-flash"
    
    TRIPLE_TAP_WINDOW: float = float(os.getenv("TRIPLE_TAP_WINDOW", "0.5"))
    TAP_DETECTION_RADIUS: int = 50
    CROP_BOX: list = None
    RESPONSE_DURATION: float = float(os.getenv("RESPONSE_DURATION", "2.0"))
    RESPONSE_FONT_SIZE: int = 13
    RESPONSE_TEXT_COLOR: list = field(default_factory=lambda: [255, 255, 255])
    RESPONSE_BG_COLOR: list = field(default_factory=lambda: [0, 0, 0])
    RESPONSE_OPACITY: float = 0.95
    INJECT_X: int = 80
    INJECT_Y: int = 80
    INJECT_WIDTH: int = 1200
    INJECT_MAX_HEIGHT: int = 400
    MAX_RESPONSE_LENGTH: int = 300
    API_TIMEOUT: int = 20
    GLOBAL_SHORTCUT: str = os.getenv("GLOBAL_SHORTCUT", "Ctrl+Shift+S")
    HIDE_PROCESS: bool = os.getenv("HIDE_PROCESS", "true").lower() == "true"
    HIDE_CONSOLE: bool = os.getenv("HIDE_CONSOLE", "true").lower() == "true"
    HIDE_WINDOW: bool = True
    HIDE_FROM_TASKBAR: bool = True
    DISABLE_CAPTURE_PROTECTION: bool = os.getenv("DISABLE_CAPTURE_PROTECTION", "false").lower() == "true"
    LOG_DIR: Path = Path.home() / ".novaghost"
    LOG_FILE: Path = Path.home() / ".novaghost" / "novaghost.log"
    CRASH_LOG_FILE: Path = Path.home() / ".novaghost" / "crash.log"
    TEST_LOG_FILE: Path = Path.home() / ".novaghost" / "test.log"
    SETTINGS_FILE: Path = Path.home() / ".novaghost" / "settings.json"
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    SAFE_MODE: bool = False

    def __post_init__(self):
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.load_from_disk()

    def load_from_disk(self):
        if not self.SETTINGS_FILE.exists():
            return
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8-sig") as f:
                saved_data = json.load(f)
            allowed_fields = [
                "TRIPLE_TAP_WINDOW",
                "CROP_BOX",
                "RESPONSE_DURATION",
                "RESPONSE_FONT_SIZE",
                "MAX_RESPONSE_LENGTH",
                "DEBUG_MODE",
                "GLOBAL_SHORTCUT",
                "ACTIVE_PROVIDER",
                "ACTIVE_MODEL",
                "API_KEYS",
                "FALLBACK_ENABLED",
                "FALLBACK_PROVIDER",
                "FALLBACK_MODEL",
                "OLLAMA_BASE_URL",
            ]
            for field_name in allowed_fields:
                if field_name in saved_data and hasattr(self, field_name):
                    setattr(self, field_name, saved_data[field_name])
            # Ensure ollama key always present after load
            if isinstance(self.API_KEYS, dict):
                self.API_KEYS.setdefault("ollama", "local")
            logger.info("Configuration preferences loaded from settings.json.")
        except Exception as e:
            logger.error(f"Failed to load settings.json: {e}")

    def save_to_disk(self):
        try:
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)
            serializable = {
                "TRIPLE_TAP_WINDOW": self.TRIPLE_TAP_WINDOW,
                "CROP_BOX": self.CROP_BOX,
                "RESPONSE_DURATION": self.RESPONSE_DURATION,
                "RESPONSE_FONT_SIZE": self.RESPONSE_FONT_SIZE,
                "MAX_RESPONSE_LENGTH": self.MAX_RESPONSE_LENGTH,
                "DEBUG_MODE": self.DEBUG_MODE,
                "GLOBAL_SHORTCUT": self.GLOBAL_SHORTCUT,
                "ACTIVE_PROVIDER": self.ACTIVE_PROVIDER,
                "ACTIVE_MODEL": self.ACTIVE_MODEL,
                "API_KEYS": self.API_KEYS,
                "FALLBACK_ENABLED": self.FALLBACK_ENABLED,
                "FALLBACK_PROVIDER": self.FALLBACK_PROVIDER,
                "FALLBACK_MODEL": self.FALLBACK_MODEL,
                "OLLAMA_BASE_URL": self.OLLAMA_BASE_URL,
            }
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=4)
            logger.info("Configuration saved to settings.json.")
        except Exception as e:
            logger.error(f"Failed to save settings.json: {e}")

    def get_api_key(self, provider: str) -> str:
        if provider.lower() == "ollama":
            return "local"
        return self.API_KEYS.get(provider.lower(), "")

    def set_api_key(self, provider: str, key: str) -> None:
        self.API_KEYS[provider.lower()] = key

    def has_primary_key(self) -> bool:
        return bool(self.get_api_key(self.ACTIVE_PROVIDER))

    def has_fallback_key(self) -> bool:
        if self.FALLBACK_ENABLED:
            return bool(self.get_api_key(self.FALLBACK_PROVIDER))
        return False

    def validate(self) -> bool:
        if not self.has_primary_key():
            raise ValueError(
                f"No API key configured for the active visual analysis provider '{self.ACTIVE_PROVIDER}'. "
                "Configure it in settings."
            )
        return True

config = Config()