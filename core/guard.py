import sys
import logging

logger = logging.getLogger(__name__)
_MUTEX_NAME = "Global\\VisualAnalyzerSystem_SingleInstanceMutex"
_mutex_handle = None

def acquire() -> bool:
    global _mutex_handle
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        import ctypes.wintypes
        kernel32 = ctypes.windll.kernel32
        _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if _mutex_handle == 0:
            return True
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
            return False
        return True
    except Exception as e:
        logger.error(f"Guard error: {e}")
        return True

def release() -> None:
    global _mutex_handle
    if _mutex_handle is not None:
        try:
            import ctypes
            ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
            ctypes.windll.kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
        except Exception as e:
            logger.warning(f"Guard release error: {e}")

def show_already_running_dialog() -> str:
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
        root.title("NovaGhost")
        root.geometry("420x200")
        root.resizable(False, False)
        root.configure(fg_color="#0A0B10")
        root.attributes("-topmost", True)
        root.update_idletasks()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - 420) // 2
        y = (sh - 200) // 2
        root.geometry(f"420x200+{x}+{y}")
        result = {"action": "exit"}

        ctk.CTkLabel(
            root,
            text="⚡ Portal Connection",
            font=ctk.CTkFont(family="Segoe UI Variable", size=18, weight="bold"),
            text_color="#6366F1"
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            root,
            text="The portal client is already active in the background.",
            font=ctk.CTkFont(family="Segoe UI Variable", size=12),
            text_color="#9CA3AF"
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30)

        def on_open():
            result["action"] = "focus"
            root.destroy()

        def on_exit():
            result["action"] = "exit"
            root.destroy()

        ctk.CTkButton(
            btn_frame,
            text="Open Client",
            fg_color="#6366F1",
            hover_color="#4F46E5",
            height=36,
            corner_radius=10,
            command=on_open
        ).pack(side="left", expand=True, padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Exit",
            fg_color="transparent",
            border_width=1,
            border_color="#374151",
            text_color="#9CA3AF",
            hover_color="#1F2937",
            height=36,
            corner_radius=10,
            command=on_exit
        ).pack(side="right", expand=True, padx=(8, 0))

        root.mainloop()
        return result["action"]
    except Exception as e:
        logger.error(f"Guard dialog error: {e}")
        return "exit"

def focus_existing_instance() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        HWND_FOUND = ctypes.wintypes.HWND(0)

        def enum_callback(hwnd, lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "NovaGhost" in buf.value:
                HWND_FOUND.value = hwnd
                return False
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        if HWND_FOUND.value:
            SW_RESTORE = 9
            user32.ShowWindow(HWND_FOUND.value, SW_RESTORE)
            user32.SetForegroundWindow(HWND_FOUND.value)
            return True
        return False
    except Exception as e:
        logger.error(f"Guard focus error: {e}")
        return False
