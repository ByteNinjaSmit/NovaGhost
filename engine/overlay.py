import logging
import tkinter as tk
import threading
from config import Config

logger = logging.getLogger(__name__)

class OverlayController:
    def __init__(self, config: Config, parent=None):
        self.config = config
        self.parent = parent

    def inject_response(self, text: str) -> bool:
        return self.display_response(text)

    def display_response(self, text: str) -> bool:
        try:
            logger.debug(f"Rendering overlay text: {text}")
            clean_token = text.strip()
            if not clean_token:
                clean_token = "?"
            if self.parent:
                self.parent.after(0, lambda: self._show_overlay(clean_token))
            else:
                overlay_thread = threading.Thread(target=self._show_overlay, args=(clean_token,), daemon=True)
                overlay_thread.start()
            return True
        except Exception as e:
            logger.error(f"Overlay rendering failed: {e}")
            return False

    def _show_overlay(self, clean_option: str):
        try:
            if self.parent:
                root = tk.Toplevel(self.parent)
            else:
                root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.wm_attributes("-transparentcolor", "black")
            root.config(bg="black")
            font_size = max(6, int(self.config.RESPONSE_FONT_SIZE * 0.7))
            font_config = ("Consolas", font_size, "bold")
            hex_color = '#%02x%02x%02x' % tuple(self.config.RESPONSE_TEXT_COLOR)
            label = tk.Label(root, text=clean_option, font=font_config, fg=hex_color, bg="black", justify="left")
            label.place(x=0, y=0)
            root.update_idletasks()
            width = label.winfo_reqwidth() + 10
            height = label.winfo_reqheight() + 10
            root.geometry(f"{width}x{height}+{self.config.INJECT_X}+{self.config.INJECT_Y}")
            self._apply_styles(root)
            duration_ms = int(self.config.RESPONSE_DURATION * 1000)
            root.after(duration_ms, root.destroy)
            if not self.parent:
                root.mainloop()
        except Exception as e:
            logger.error(f"Overlay rendering exception: {e}")

    def _apply_styles(self, root: tk.Tk):
        import sys
        if sys.platform != 'win32':
            return
        import ctypes
        try:
            root.update()
            hwnd = root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_LAYERED = 0x00080000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = style | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_LAYERED
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 1)
            if not self.config.DISABLE_CAPTURE_PROTECTION:
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                success = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        except Exception as e:
            logger.error(f"Failed to apply overlay styles: {e}")
            
    def inject_overlay(self, text: str) -> bool:
        return self.display_response(text)
