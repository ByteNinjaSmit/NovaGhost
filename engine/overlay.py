"""
NovaGhost — Advanced Response Overlay System.
Displays complete answers with zero clipping, dynamic height, scrollable area,
high contrast, copy-to-clipboard, manual close, and clear answer hierarchy.
"""

import sys
import logging
import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Any
from config import Config

logger = logging.getLogger(__name__)


class ModernOverlayWindow:
    """Modern floating overlay window with clear visual hierarchy, scrolling, and action buttons."""

    def __init__(self, config: Config, parent=None):
        self.config = config
        self.parent = parent
        self.root: Optional[tk.Toplevel] = None
        self._close_timer = None

    def show(self, text: str, multi_res: Optional[Any] = None) -> None:
        try:
            self._destroy_existing()

            if self.parent:
                self.root = tk.Toplevel(self.parent)
            else:
                self.root = tk.Tk()

            # Window configuration
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            self.root.config(bg="#0E1017")

            # Colors
            bg_dark = "#0E1017"
            card_bg = "#161922"
            accent_blue = "#6366F1"
            text_white = "#F3F4F6"
            text_dim = "#9CA3AF"
            success_green = "#10B981"
            warn_amber = "#F59E0B"

            current_displayed_text = text.strip()

            # Outer frame with glowing border
            border_frame = tk.Frame(self.root, bg=accent_blue, padx=1, pady=1)
            border_frame.pack(fill="both", expand=True)

            main_container = tk.Frame(border_frame, bg=bg_dark, padx=12, pady=10)
            main_container.pack(fill="both", expand=True)

            # Top Header Bar: Category / Status and Actions
            header_bar = tk.Frame(main_container, bg=bg_dark)
            header_bar.pack(fill="x", pady=(0, 4))

            # Title Badge
            is_cached = getattr(multi_res, "is_cached", False)
            is_multi = getattr(multi_res, "is_multi_question", False)
            q_count = len(getattr(multi_res, "questions", [])) if is_multi else 1

            if is_cached:
                badge_text = "⚡ NOVAGHOST (Instant Cache)"
                badge_color = success_green
            elif is_multi:
                badge_text = f"⚡ MULTI-QUESTION ({q_count} Questions)"
                badge_color = "#38BDF8"  # Light blue
            elif text.startswith("SCREENSHOT UNCLEAR"):
                badge_text = "⚠️ SCREENSHOT UNCLEAR"
                badge_color = warn_amber
            elif text.startswith("API Error") or "failed" in text.lower():
                badge_text = "❌ SYSTEM NOTICE"
                badge_color = "#EF4444"
            else:
                badge_text = "⚡ NOVAGHOST ANSWER"
                badge_color = success_green

            badge_lbl = tk.Label(
                header_bar,
                text=badge_text,
                font=("Segoe UI", 9, "bold"),
                fg=badge_color,
                bg=bg_dark
            )
            badge_lbl.pack(side="left")

            # Action Buttons: Copy and Close
            btn_frame = tk.Frame(header_bar, bg=bg_dark)
            btn_frame.pack(side="right")

            def on_copy():
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(current_displayed_text)
                    copy_btn.config(text="✓ Copied", fg=success_green)
                    self.root.after(1200, lambda: copy_btn.config(text="📋 Copy", fg=text_dim))
                except Exception as e:
                    logger.debug(f"Copy error: {e}")

            copy_btn = tk.Button(
                btn_frame,
                text="📋 Copy",
                font=("Segoe UI", 8),
                fg=text_dim,
                bg=card_bg,
                activebackground=accent_blue,
                activeforeground="#FFFFFF",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=on_copy
            )
            copy_btn.pack(side="left", padx=(0, 6))

            close_btn = tk.Button(
                btn_frame,
                text="✕",
                font=("Segoe UI", 9, "bold"),
                fg=text_dim,
                bg=card_bg,
                activebackground="#EF4444",
                activeforeground="#FFFFFF",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=self._destroy_existing
            )
            close_btn.pack(side="left")

            # Optional Multi-Question Tab Bar
            tab_buttons = []
            if is_multi and hasattr(multi_res, "questions"):
                tab_bar = tk.Frame(main_container, bg=bg_dark)
                tab_bar.pack(fill="x", pady=(2, 6))

                def select_tab(idx: Optional[int]):
                    nonlocal current_displayed_text
                    if idx is None:
                        current_displayed_text = multi_res.to_strict_format(None)
                    else:
                        current_displayed_text = multi_res.to_strict_format(idx)

                    for b_idx, btn in enumerate(tab_buttons):
                        if (idx is None and b_idx == len(tab_buttons) - 1) or (b_idx == idx):
                            btn.config(bg=accent_blue, fg="#FFFFFF")
                        else:
                            btn.config(bg=card_bg, fg=text_dim)

                    text_widget.config(state="normal")
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", current_displayed_text.strip())
                    text_widget.config(state="disabled")

                for i in range(len(multi_res.questions)):
                    tb = tk.Button(
                        tab_bar,
                        text=f"Q{i+1}",
                        font=("Segoe UI", 8, "bold"),
                        fg=text_dim,
                        bg=card_bg,
                        activebackground=accent_blue,
                        activeforeground="#FFFFFF",
                        bd=0,
                        padx=8,
                        pady=2,
                        cursor="hand2",
                        command=lambda q_idx=i: select_tab(q_idx)
                    )
                    tb.pack(side="left", padx=(0, 4))
                    tab_buttons.append(tb)

                all_btn = tk.Button(
                    tab_bar,
                    text="ALL",
                    font=("Segoe UI", 8, "bold"),
                    fg="#FFFFFF",
                    bg=accent_blue,
                    activebackground=accent_blue,
                    activeforeground="#FFFFFF",
                    bd=0,
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    command=lambda: select_tab(None)
                )
                all_btn.pack(side="left")
                tab_buttons.append(all_btn)

                # Bind number keys 1, 2, 3, etc. to switch tabs
                for i in range(len(multi_res.questions)):
                    self.root.bind(str(i + 1), lambda e, q_idx=i: select_tab(q_idx))
                self.root.bind("0", lambda e: select_tab(None))
                self.root.bind("a", lambda e: select_tab(None))

            # Answer Content Card with Scrollable Text
            content_card = tk.Frame(main_container, bg=card_bg, padx=10, pady=8)
            content_card.pack(fill="both", expand=True)

            font_size = max(11, self.config.RESPONSE_FONT_SIZE)

            # Scrollable Text Widget to prevent any truncation
            scrollbar = tk.Scrollbar(content_card, width=10, bg=card_bg)
            text_widget = tk.Text(
                content_card,
                font=("Consolas", font_size, "bold"),
                fg=text_white,
                bg=card_bg,
                wrap="word",
                bd=0,
                padx=4,
                pady=4,
                highlightthickness=0,
                cursor="arrow",
                yscrollcommand=scrollbar.set
            )
            scrollbar.config(command=text_widget.yview)
            text_widget.insert("1.0", text.strip())
            text_widget.config(state="disabled")
            text_widget.bind("<MouseWheel>", lambda event: text_widget.yview_scroll(int(-1*(event.delta/120)), "units"))
            
            scrollbar.pack(side="right", fill="y")
            text_widget.pack(side="left", fill="both", expand=True)

            # Auto-calculate optimal width and height
            lines = text.strip().split("\n")
            line_count = len(lines)
            max_line_len = max([len(l) for l in lines] if lines else [1])

            calc_width = min(850, max(400, max_line_len * 12 + 60))
            calc_height = min(500, max(120, line_count * (font_size + 14) + (80 if is_multi else 60)))

            x = self.config.INJECT_X
            y = self.config.INJECT_Y
            self.root.geometry(f"{calc_width}x{calc_height}+{x}+{y}")

            # Enable window drag so user can reposition if needed
            self._make_draggable(main_container)
            self._make_draggable(header_bar)

            # Bind Escape key to close
            self.root.bind("<Escape>", lambda e: self._destroy_existing())

            # Apply Windows stealth and click-through/topmost attributes
            self._apply_windows_styles(self.root)

            # Auto-dismiss timer (pauses if mouse hovers over overlay)
            duration_sec = max(2.5, self.config.RESPONSE_DURATION)
            duration_ms = int(duration_sec * 1000)

            def cancel_auto_close(event):
                if self._close_timer:
                    self.root.after_cancel(self._close_timer)
                    self._close_timer = None

            def schedule_auto_close(event=None):
                if not self._close_timer and self.root:
                    self._close_timer = self.root.after(duration_ms, self._destroy_existing)

            self.root.bind("<Enter>", cancel_auto_close)
            self.root.bind("<Leave>", schedule_auto_close)
            self._close_timer = self.root.after(duration_ms, self._destroy_existing)

            if not self.parent:
                self.root.mainloop()

        except Exception as e:
            logger.error(f"Error in overlay display: {e}", exc_info=True)

    def _make_draggable(self, widget):
        start_x = 0
        start_y = 0

        def on_drag_start(event):
            nonlocal start_x, start_y
            start_x = event.x
            start_y = event.y

        def on_drag_motion(event):
            if not self.root:
                return
            deltax = event.x - start_x
            deltay = event.y - start_y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        widget.bind("<Button-1>", on_drag_start)
        widget.bind("<B1-Motion>", on_drag_motion)

    def _destroy_existing(self):
        if self._close_timer and self.root:
            try:
                self.root.after_cancel(self._close_timer)
            except Exception:
                pass
            self._close_timer = None

        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None

    def _apply_windows_styles(self, root: tk.Tk):
        if sys.platform != 'win32':
            return
        import ctypes
        from ctypes import wintypes
        try:
            root.update()
            hwnd_raw = root.winfo_id()
            GA_ROOT = 2
            h_root = ctypes.windll.user32.GetAncestor(hwnd_raw, GA_ROOT)
            target_hwnd = h_root if (h_root and h_root != 0) else hwnd_raw

            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_LAYERED = 0x00080000
            style = ctypes.windll.user32.GetWindowLongW(target_hwnd, GWL_EXSTYLE)
            new_style = style | WS_EX_NOACTIVATE | WS_EX_LAYERED
            ctypes.windll.user32.SetWindowLongW(target_hwnd, GWL_EXSTYLE, new_style)

            # Apply robust screen capture exclusion via SetWindowDisplayAffinity
            if not self.config.DISABLE_CAPTURE_PROTECTION:
                WDA_NONE = 0x00000000
                WDA_MONITOR = 0x00000001
                WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+ and Windows 11

                # Apply to root window handle and verify
                res = ctypes.windll.user32.SetWindowDisplayAffinity(target_hwnd, WDA_EXCLUDEFROMCAPTURE)
                if not res:
                    # Fallback to WDA_MONITOR for older Windows builds
                    res = ctypes.windll.user32.SetWindowDisplayAffinity(target_hwnd, WDA_MONITOR)
                    logger.info(f"Overlay capture protection applied: WDA_MONITOR (status: {bool(res)})")
                else:
                    affinity = wintypes.DWORD()
                    ctypes.windll.user32.GetWindowDisplayAffinity(target_hwnd, ctypes.byref(affinity))
                    logger.info(f"Overlay capture protection applied: WDA_EXCLUDEFROMCAPTURE (affinity: {hex(affinity.value)})")

            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(
                target_hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        except Exception as e:
            logger.debug(f"Failed to apply overlay window styles: {e}")


class OverlayController:
    """Manages overlay lifecycle and rendering."""

    def __init__(self, config: Config, parent=None):
        self.config = config
        self.parent = parent
        self._overlay_window = ModernOverlayWindow(config, parent=parent)

    def display_response(self, text: str, multi_res: Optional[Any] = None) -> bool:
        try:
            logger.debug(f"Rendering overlay text:\n{text}")
            clean_token = text.strip()
            if not clean_token:
                clean_token = "?"

            if self.parent:
                self.parent.after(0, lambda: self._overlay_window.show(clean_token, multi_res))
            else:
                t = threading.Thread(target=self._overlay_window.show, args=(clean_token, multi_res), daemon=True)
                t.start()
            return True
        except Exception as e:
            logger.error(f"Overlay rendering failed: {e}")
            return False

    def inject_response(self, text: str) -> bool:
        return self.display_response(text)

    def inject_overlay(self, text: str) -> bool:
        return self.display_response(text)
