import logging
import threading
import customtkinter as ctk
from pathlib import Path
from typing import Callable, Optional
import queue
import tkinter as tk

from config import config
from ui.components.side import Sidebar
from ui.views.diag import DiagnosticsView
from ui.views.main import DashboardView
from ui.views.settings import PreferencesView
from ui.views.info import ReleaseNotesView
import core.safe as safe_mode

logger = logging.getLogger("AppWindow")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_COLORS = {
    "bg":      "#0A0B10",
    "surface": "#12141C",
    "border":  "#252838",
    "text":    "#F3F4F6",
    "muted":   "#9CA3AF",
    "accent":  "#6366F1",
}

_main_thread = threading.current_thread()
_tkinter_after_queue = queue.Queue()
_orig_after = tk.Misc.after

def _thread_safe_after(self, ms, func=None, *args):
    if threading.current_thread() is _main_thread:
        return _orig_after(self, ms, func, *args)
    else:
        if func is not None:
            def task():
                try:
                    if self.winfo_exists():
                        _orig_after(self, ms, func, *args)
                except Exception:
                    pass
            _tkinter_after_queue.put(task)
        return None

tk.Misc.after = _thread_safe_after

class ActivationWindow(ctk.CTk):
    def __init__(
        self,
        on_ready: Optional[Callable] = None,
        on_start_engine: Optional[Callable] = None,
        on_stop_engine: Optional[Callable] = None,
        on_shortcut_changed: Optional[Callable] = None,
    ):
        super().__init__()
        self.on_ready = on_ready
        self.on_start_engine = on_start_engine
        self.on_stop_engine = on_stop_engine
        self.on_shortcut_changed = on_shortcut_changed
        # Local-only build: always "authenticated". Kept for backward compatibility
        # with views that still check this flag.
        self.is_authenticated: bool = True
        self.engine_running: bool = False
        self._views: dict = {}
        self._current_tab: str = ""
        self._setup_window()
        self._setup_layout()
        self._start()
        self._process_after_queue()

    def _process_after_queue(self):
        try:
            while True:
                task = _tkinter_after_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    logger.error(f"Error in thread-safe after task: {e}")
        except queue.Empty:
            pass
        _orig_after(self, 50, self._process_after_queue)

    def _setup_window(self) -> None:
        self.title("NovaGhost")
        self.geometry("980x660")
        self.resizable(True, True)
        self.minsize(980, 640)
        self.configure(fg_color=_COLORS["bg"])
        bg_path = Path(__file__).parent / "bg.png"
        if bg_path.exists():
            try:
                from PIL import Image
                self._bg_image_original = Image.open(bg_path)
                img = ctk.CTkImage(
                    light_image=self._bg_image_original,
                    dark_image=self._bg_image_original,
                    size=(980, 660)
                )
                bg_lbl = ctk.CTkLabel(self, image=img, text="")
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
                self.bind("<Configure>", self._on_resize)
                self._bg_label = bg_lbl
            except Exception as e:
                logger.warning(f"Background image failed to load: {e}")
        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self._sidebar = Sidebar(
            self,
            on_nav=self._navigate_to,
            on_diagnostics=lambda: self._navigate_to("diag"),
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)
        self._status_bar = ctk.CTkLabel(
            self._content,
            text="",
            font=ctk.CTkFont(family="Segoe UI Variable", size=11),
            text_color=_COLORS["muted"],
            anchor="w",
            height=20
        )
        self._status_bar.grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def _start(self) -> None:
        if safe_mode.is_active():
            logger.warning("Safe Mode active — opening Diagnostics Center.")
            self._sidebar.show_safe_mode_indicator()
            self._navigate_to("diag")
            return
        self._sidebar.show_nav()
        if self.on_ready:
            # Defer to the next loop tick so module-level globals in the
            # callback (e.g. the app_window reference) are bound first.
            self.after(0, self._fire_on_ready)
        self._navigate_to("dash")
        self._sidebar.refresh_health_async()
        if not config.has_primary_key():
            self._set_status(
                "No API key set — open Preferences and enter your API key to use the scanner."
            )

    def _fire_on_ready(self) -> None:
        try:
            self.on_ready()
        except Exception as e:
            logger.error(f"on_ready callback error: {e}")

    def _navigate_to(self, tab: str) -> None:
        if self._current_tab == tab:
            return
        if self._current_tab:
            curr_view = self._views.get(self._current_tab)
            if curr_view:
                curr_view.grid_remove()
        self._current_tab = tab
        self._sidebar.set_active_tab(tab)
        self._set_status("")
        view = self._get_or_create_view(tab)
        if view:
            view.grid(row=0, column=0, sticky="nsew")
            if hasattr(view, "on_show"):
                try:
                    view.on_show()
                except Exception as e:
                    logger.error(f"Error calling on_show for {tab}: {e}")

    def _get_or_create_view(self, tab: str) -> Optional[ctk.CTkFrame]:
        if tab in self._views:
            return self._views[tab]
        view_factories = {
            "dash":  self._make_dashboard_view,
            "pref":  self._make_preferences_view,
            "notes": self._make_release_notes_view,
            "diag":  self._make_diagnostics_view,
        }
        factory = view_factories.get(tab)
        if factory:
            view = factory()
            self._views[tab] = view
            return view
        return None

    def _make_dashboard_view(self) -> ctk.CTkFrame:
        return DashboardView(
            self._content,
            on_start_engine=self._start_engine,
            on_stop_engine=self._stop_engine,
            on_select_region=self._select_screen_region,
            engine_running=self.engine_running,
        )

    def _make_preferences_view(self) -> ctk.CTkFrame:
        return PreferencesView(
            self._content,
            on_shortcut_changed=self.on_shortcut_changed,
            on_select_region=self._select_screen_region,
        )

    def _make_release_notes_view(self) -> ctk.CTkFrame:
        return ReleaseNotesView(self._content)

    def _make_diagnostics_view(self) -> ctk.CTkFrame:
        return DiagnosticsView(self._content)

    def _start_engine(self) -> None:
        if self.engine_running:
            return
        if safe_mode.is_active():
            self._set_status("Cannot start engine in Safe Mode.")
            return
        self.engine_running = True
        if self.on_start_engine:
            try:
                self.on_start_engine()
            except Exception as e:
                logger.error(f"Engine start error: {e}")
                self.engine_running = False

    def _stop_engine(self) -> None:
        if not self.engine_running:
            return
        self.engine_running = False
        if self.on_stop_engine:
            try:
                self.on_stop_engine()
            except Exception as e:
                logger.error(f"Engine stop error: {e}")

    def _select_screen_region(self) -> None:
        from engine.capture import ScreenCaptureManager
        try:
            cap = ScreenCaptureManager(config, parent=self)
            cap.request_screen_selection(parent=self)
        except Exception as e:
            logger.error(f"Region selection error: {e}")

    def _set_status(self, message: str) -> None:
        self._status_bar.configure(text=message)

    def _on_resize(self, event) -> None:
        if hasattr(self, "_resize_job"):
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = _orig_after(self, 150, self._apply_bg_resize)

    def _apply_bg_resize(self) -> None:
        try:
            if hasattr(self, "_bg_label") and hasattr(self, "_bg_image_original"):
                w = self.winfo_width()
                h = self.winfo_height()
                if w < 10 or h < 10:
                    return
                last = getattr(self, "_bg_last_size", None)
                if last == (w, h):
                    return
                self._bg_last_size = (w, h)
                new_img = ctk.CTkImage(
                    light_image=self._bg_image_original,
                    dark_image=self._bg_image_original,
                    size=(w, h)
                )
                self._bg_label.configure(image=new_img)
        except Exception:
            pass

    def _on_close(self) -> None:
        if self.engine_running and self.on_stop_engine:
            try:
                self.on_stop_engine()
            except Exception:
                pass
        from core.guard import release as release_mutex
        release_mutex()
        self.destroy()
