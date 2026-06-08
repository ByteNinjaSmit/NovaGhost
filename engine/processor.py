import logging
import threading
import queue
import time
from config import Config
from engine.detector import InputDetector
from engine.capture import ScreenCaptureManager
from network.api_client import ApiClient
from engine.overlay import OverlayController
from engine.hider import VisibilityController
from utils.log import log_exception, add_recent_event

logger = logging.getLogger(__name__)

class PipelineManager:
    def __init__(self, config: Config, parent=None):
        self.config = config
        self.parent = parent
        self.gesture_detector = InputDetector(
            config.TRIPLE_TAP_WINDOW,
            config.TAP_DETECTION_RADIUS
        )
        self.capture_manager = ScreenCaptureManager(config, parent=parent)
        if not self.config.CROP_BOX:
            self.capture_manager.request_screen_selection(parent=parent)
        self.api_handler = ApiClient(config)
        self.injection = OverlayController(config, parent=parent)
        self.task_queue = queue.Queue()
        self.processing = False
        self.running = True
        self._last_request_time: float = 0.0
        self._request_cooldown: float = 5.0
        if config.HIDE_PROCESS:
            VisibilityController.hide_console()
            VisibilityController.hide_from_taskbar()

    def _process_pipeline(self) -> None:
        while self.running:
            try:
                self.task_queue.get(timeout=1)
                if self.processing:
                    continue
                self.processing = True
                self._last_request_time = time.time()
                add_recent_event("Pipeline trigger received")
                screenshot = self.capture_manager.capture_screen()
                if not screenshot:
                    self.processing = False
                    continue
                add_recent_event("Screen region captured")
                if self.parent and hasattr(self.parent, "_credit_service") and self.parent._credit_service:
                    ok, msg = self.parent._credit_service.check_and_consume()
                    if not ok:
                        self.injection.display_response("No resources available.")
                        self.processing = False
                        if hasattr(self.parent, "_refresh_credits_background"):
                            self.parent._refresh_credits_background()
                        continue
                response = self.api_handler.query(screenshot)
                if not response:
                    err = getattr(self.api_handler, "_last_error", "") or "check API key / model name"
                    self.injection.display_response(f"API Error: {err}")
                    self.processing = False
                    continue
                add_recent_event(f"Query returned: {len(response)} chars")
                self.injection.display_response(response)
                self.processing = False
                if self.parent and hasattr(self.parent, "_refresh_credits_background"):
                    self.parent._refresh_credits_background()
            except queue.Empty:
                continue
            except Exception as e:
                log_exception(logger, "PipelineManager", "_process_pipeline", e)
                self.processing = False

    def _on_gesture_detected(self) -> None:
        now = time.time()
        if self.processing:
            return
        elapsed = now - self._last_request_time
        if elapsed < self._request_cooldown:
            remaining = int(self._request_cooldown - elapsed) + 1
            self.injection.display_response(f"Wait {remaining}s")
            return
        add_recent_event("Trigger detected")
        self.task_queue.put(True)

    def start(self) -> None:
        self.gesture_detector.set_callback(self._on_gesture_detected)
        processor = threading.Thread(
            target=self._process_pipeline,
            daemon=True,
            name="PipelineProcessor"
        )
        processor.start()
        gesture_thread = threading.Thread(
            target=self.gesture_detector.start,
            daemon=True,
            name="GestureListener"
        )
        gesture_thread.start()

    def shutdown(self) -> None:
        self.running = False
        self.gesture_detector.stop()

class StealthSystem(PipelineManager):
    pass
