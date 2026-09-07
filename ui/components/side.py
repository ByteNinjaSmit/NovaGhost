import threading
import customtkinter as ctk
from typing import Callable, Dict

from config import config
from services import status_service

class Sidebar(ctk.CTkFrame):
    HEALTH_ITEMS = [
        ("internet",      "Internet"),
        ("visual_system", "Visual System"),
        ("ai_engine",     "AI Engine"),
        ("storage",       "Storage"),
    ]

    NAV_ITEMS = [
        ("dash",  "  Dashboard",     2),
        ("pref",  "  Preferences",   3),
        ("notes", "  Release Notes", 4),
        ("diag",  "  Diagnostics",   5),
    ]

    def __init__(
        self,
        parent,
        on_nav: Callable[[str], None],
        on_diagnostics: Callable,
        **kwargs
    ):
        super().__init__(
            parent,
            width=220,
            corner_radius=0,
            fg_color="#0A0B10",
            border_width=1,
            border_color="#1A1C28",
            **kwargs
        )
        self.on_nav = on_nav
        self.on_diagnostics = on_diagnostics
        self._nav_buttons: Dict[str, ctk.CTkButton] = {}
        self._health_indicators: Dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(
            self,
            text="NOVAGHOST",
            font=ctk.CTkFont(family="Segoe UI Variable", size=22, weight="bold"),
            text_color="#6366F1"
        ).grid(row=0, column=0, padx=20, pady=(24, 2))
        ctk.CTkLabel(
            self,
            text="by Twistark Technologies",
            text_color="#6B7280",
            font=ctk.CTkFont(family="Segoe UI Variable", size=10, weight="bold")
        ).grid(row=1, column=0, padx=20, pady=(0, 16))
        for tab, label, row in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color="#9CA3AF",
                hover_color="#12141C",
                corner_radius=8,
                height=36,
                command=lambda t=tab: self._on_nav_click(t),
                font=ctk.CTkFont(family="Segoe UI Variable", size=12, weight="bold")
            )
            btn.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
            self._nav_buttons[tab] = btn
        self._build_health_panel()
        self._build_client_panel()

    def _build_health_panel(self) -> None:
        health_frame = ctk.CTkFrame(self, fg_color="transparent")
        health_frame.grid(row=9, column=0, padx=12, pady=(10, 2), sticky="ew")
        ctk.CTkLabel(
            health_frame,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(family="Segoe UI Variable", size=10, weight="bold"),
            text_color="#6B7280",
            anchor="w"
        ).pack(fill="x", padx=5, pady=(0, 4))
        health_grid = ctk.CTkFrame(health_frame, fg_color="transparent")
        health_grid.pack(fill="x", padx=5)
        health_grid.grid_columnconfigure(0, weight=1)
        health_grid.grid_columnconfigure(1, weight=1)
        for idx, (key, name) in enumerate(self.HEALTH_ITEMS):
            row = idx // 2
            col = idx % 2
            item = ctk.CTkFrame(health_grid, fg_color="transparent", height=18)
            item.grid(row=row, column=col, sticky="ew", pady=1)
            lbl = ctk.CTkLabel(
                item,
                text=f"🟡 {name}",
                font=ctk.CTkFont(family="Segoe UI Variable", size=9, weight="bold"),
                text_color="#9CA3AF",
                anchor="w"
            )
            lbl.pack(fill="x", side="left")
            self._health_indicators[key] = lbl

    def _build_client_panel(self) -> None:
        client_frame = ctk.CTkFrame(self, fg_color="transparent")
        client_frame.grid(row=10, column=0, padx=12, pady=(5, 12), sticky="ew")
        ctk.CTkLabel(
            client_frame,
            text="CLIENT INFO",
            font=ctk.CTkFont(family="Segoe UI Variable", size=10, weight="bold"),
            text_color="#6B7280",
            anchor="w"
        ).pack(fill="x", padx=5, pady=(0, 3))
        label_style = {
            "font": ctk.CTkFont(family="Segoe UI Variable", size=10),
            "text_color": "#9CA3AF",
            "anchor": "w",
            "height": 15
        }
        self._lbl_version = ctk.CTkLabel(
            client_frame, text=f"Version: {config.CURRENT_VERSION}", **label_style
        )
        self._lbl_version.pack(fill="x", padx=5)
        self._lbl_provider = ctk.CTkLabel(
            client_frame, text=f"Provider: {config.ACTIVE_PROVIDER}", **label_style
        )
        self._lbl_provider.pack(fill="x", padx=5)
        self._lbl_model = ctk.CTkLabel(
            client_frame, text=f"Model: {config.ACTIVE_MODEL}", **label_style
        )
        self._lbl_model.pack(fill="x", padx=5)

    def show_nav(self) -> None:
        for tab, _, row in self.NAV_ITEMS:
            self._nav_buttons[tab].grid(
                row=row, column=0, padx=12, pady=2, sticky="ew"
            )
        self.refresh_client_info()

    def refresh_client_info(self) -> None:
        self._lbl_provider.configure(text=f"Provider: {config.ACTIVE_PROVIDER}")
        self._lbl_model.configure(text=f"Model: {config.ACTIVE_MODEL}")

    def set_active_tab(self, tab_name: str) -> None:
        tab_colors = {
            "dash":  ("#1E1C2E", "#6366F1"),
            "pref":  ("#1E1C2E", "#6366F1"),
            "notes": ("#1E1C2E", "#9CA3AF"),
            "diag":  ("#1B1A10", "#F59E0B"),
        }
        for key, btn in self._nav_buttons.items():
            if key == tab_name:
                fg, text = tab_colors.get(key, ("transparent", "#6366F1"))
                btn.configure(fg_color=fg, text_color=text)
            else:
                btn.configure(fg_color="transparent", text_color="#9CA3AF")

    def apply_health_status(self, status: Dict[str, str]) -> None:
        color_map = {
            "green":  ("🟢", "#10B981"),
            "yellow": ("🟡", "#F59E0B"),
            "red":    ("🔴", "#EF4444"),
        }
        for key, indicator_lbl in self._health_indicators.items():
            display_name = dict(self.HEALTH_ITEMS).get(key, key)
            dot, _ = color_map.get(status.get(key, "red"), ("🔴", "#EF4444"))
            indicator_lbl.configure(text=f"{dot} {display_name}")

    def refresh_health_async(self) -> None:
        def _run():
            try:
                status = status_service.check_all()
                self.after(0, lambda: self.apply_health_status(status))
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    def show_safe_mode_indicator(self) -> None:
        indicator = ctk.CTkLabel(
            self,
            text="⚠ SAFE MODE ACTIVE",
            font=ctk.CTkFont(family="Segoe UI Variable", size=11, weight="bold"),
            text_color="#F59E0B",
            fg_color="#1F1700",
            corner_radius=6,
            height=30
        )
        indicator.grid(row=0, column=0, padx=12, pady=(4, 0), sticky="ew")
        # In safe mode only Diagnostics is reachable.
        self._nav_buttons["diag"].grid(row=5, column=0, padx=12, pady=2, sticky="ew")

    def _on_nav_click(self, tab_name: str) -> None:
        self.set_active_tab(tab_name)
        self.on_nav(tab_name)
