import logging
import threading
import customtkinter as ctk
from typing import Callable, Optional

logger = logging.getLogger("AuthView")

_COLORS = {
    "bg":       "#0A0B10",
    "surface":  "#12141C",
    "border":   "#252838",
    "accent":   "#6366F1",
    "accent_hover": "#4F46E5",
    "text":     "#F3F4F6",
    "muted":    "#9CA3AF",
    "pass":     "#22C55E",
    "fail":     "#EF4444",
}

class AuthView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        handler,
        on_login_success: Callable[[dict], None],
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.handler = handler
        self.on_login_success = on_login_success
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        card = ctk.CTkFrame(
            self,
            width=420,
            height=460,
            fg_color=_COLORS["surface"],
            border_width=1,
            border_color=_COLORS["border"],
            corner_radius=16
        )
        card.grid(row=1, column=0, sticky="")
        card.grid_propagate(False)
        tab_bar = ctk.CTkFrame(card, fg_color="#181B27", corner_radius=8, height=36)
        tab_bar.pack(fill="x", padx=25, pady=(20, 0))
        tab_bar.pack_propagate(False)
        self._btn_tab_signin = ctk.CTkButton(
            tab_bar,
            text="Sign In",
            height=32,
            corner_radius=6,
            fg_color=_COLORS["accent"],
            hover_color="#818CF8",
            text_color=_COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=12, weight="bold"),
            command=lambda: self._switch_tab("signin")
        )
        self._btn_tab_signin.pack(side="left", fill="both", expand=True, padx=(4, 2), pady=2)
        self._btn_tab_signup = ctk.CTkButton(
            tab_bar,
            text="Create Account",
            height=32,
            corner_radius=6,
            fg_color="transparent",
            hover_color=_COLORS["border"],
            text_color=_COLORS["muted"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=12, weight="bold"),
            command=lambda: self._switch_tab("signup")
        )
        self._btn_tab_signup.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=2)
        content_area = ctk.CTkFrame(card, fg_color="transparent")
        content_area.pack(fill="both", expand=True, padx=25, pady=(8, 0))
        self._tab_signin = ctk.CTkFrame(content_area, fg_color="transparent")
        self._tab_signin.pack(fill="both", expand=True)
        self._tab_signup = ctk.CTkFrame(content_area, fg_color="transparent")
        self._build_signin_tab()
        self._build_signup_tab()
        self._lbl_status = ctk.CTkLabel(
            card,
            text="",
            text_color=_COLORS["fail"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=12, weight="bold")
        )
        self._lbl_status.pack(side="bottom", fill="x", pady=(0, 10))
        self._active_tab = "signin"
        ctk.CTkLabel(
            self,
            text="A Product of Twistark Technologies",
            text_color="#4B5563",
            font=ctk.CTkFont(family="Segoe UI Variable", size=10)
        ).grid(row=2, column=0, pady=(10, 0))

    def _switch_tab(self, tab: str) -> None:
        if tab == "signin":
            self._tab_signup.pack_forget()
            self._tab_signin.pack(fill="both", expand=True)
            self._btn_tab_signin.configure(fg_color=_COLORS["accent"], text_color=_COLORS["text"])
            self._btn_tab_signup.configure(fg_color="transparent", text_color=_COLORS["muted"])
        else:
            self._tab_signin.pack_forget()
            self._tab_signup.pack(fill="both", expand=True)
            self._btn_tab_signup.configure(fg_color=_COLORS["accent"], text_color=_COLORS["text"])
            self._btn_tab_signin.configure(fg_color="transparent", text_color=_COLORS["muted"])
        self._active_tab = tab
        self._set_status("", False)

    def _build_signin_tab(self) -> None:
        tab = self._tab_signin
        ctk.CTkLabel(
            tab,
            text="Username:",
            font=ctk.CTkFont(family="Segoe UI Variable", weight="bold", size=12),
            text_color=_COLORS["text"]
        ).pack(anchor="w", padx=10, pady=(15, 2))
        self._ent_login_user = ctk.CTkEntry(
            tab,
            height=38,
            placeholder_text="Username ID",
            fg_color=_COLORS["bg"],
            border_color=_COLORS["border"],
            text_color=_COLORS["text"],
            corner_radius=8
        )
        self._ent_login_user.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(
            tab,
            text="Password:",
            font=ctk.CTkFont(family="Segoe UI Variable", weight="bold", size=12),
            text_color=_COLORS["text"]
        ).pack(anchor="w", padx=10, pady=(2, 2))
        self._ent_login_pass = ctk.CTkEntry(
            tab,
            height=38,
            placeholder_text="Password",
            show="*",
            fg_color=_COLORS["bg"],
            border_color=_COLORS["border"],
            text_color=_COLORS["text"],
            corner_radius=8
        )
        self._ent_login_pass.pack(fill="x", padx=10, pady=(0, 15))
        self._sw_remember = ctk.CTkSwitch(
            tab,
            text="Remember session on this device",
            font=ctk.CTkFont(family="Segoe UI Variable", size=11),
            progress_color=_COLORS["accent"],
            text_color=_COLORS["muted"]
        )
        self._sw_remember.select()
        self._sw_remember.pack(anchor="w", padx=10, pady=5)
        self._btn_login = ctk.CTkButton(
            tab,
            text="Authenticate",
            height=42,
            font=ctk.CTkFont(family="Segoe UI Variable", size=13, weight="bold"),
            fg_color=_COLORS["accent"],
            hover_color=_COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=20,
            command=self._on_login_clicked
        )
        self._btn_login.pack(fill="x", padx=10, pady=(20, 5))
        self._ent_login_user.bind("<Return>", lambda e: self._ent_login_pass.focus())
        self._ent_login_pass.bind("<Return>", lambda e: self._on_login_clicked())

    def _build_signup_tab(self) -> None:
        tab = self._tab_signup
        ctk.CTkLabel(
            tab,
            text="Choose Username:",
            font=ctk.CTkFont(family="Segoe UI Variable", weight="bold", size=12),
            text_color=_COLORS["text"]
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self._ent_reg_user = ctk.CTkEntry(
            tab,
            height=36,
            placeholder_text="Username ID",
            fg_color=_COLORS["bg"],
            border_color=_COLORS["border"],
            text_color=_COLORS["text"],
            corner_radius=8
        )
        self._ent_reg_user.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(
            tab,
            text="Choose Password:",
            font=ctk.CTkFont(family="Segoe UI Variable", weight="bold", size=12),
            text_color=_COLORS["text"]
        ).pack(anchor="w", padx=10, pady=(2, 2))
        self._ent_reg_pass = ctk.CTkEntry(
            tab,
            height=36,
            placeholder_text="Password",
            show="*",
            fg_color=_COLORS["bg"],
            border_color=_COLORS["border"],
            text_color=_COLORS["text"],
            corner_radius=8
        )
        self._ent_reg_pass.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkLabel(
            tab,
            text="Invite / Access Key (Required):",
            font=ctk.CTkFont(family="Segoe UI Variable", weight="bold", size=11),
            text_color=_COLORS["muted"]
        ).pack(anchor="w", padx=10, pady=(2, 2))
        self._ent_reg_invite = ctk.CTkEntry(
            tab,
            height=36,
            placeholder_text="Access Code (e.g. PORTAL-XXXX)",
            fg_color=_COLORS["bg"],
            border_color=_COLORS["border"],
            text_color=_COLORS["text"],
            corner_radius=8
        )
        self._ent_reg_invite.pack(fill="x", padx=10, pady=(0, 15))
        self._btn_register = ctk.CTkButton(
            tab,
            text="Create Profile & Register",
            height=42,
            font=ctk.CTkFont(family="Segoe UI Variable", size=13, weight="bold"),
            fg_color=_COLORS["accent"],
            hover_color=_COLORS["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=20,
            command=self._on_register_clicked
        )
        self._btn_register.pack(fill="x", padx=10, pady=(5, 5))
        self._ent_reg_user.bind("<Return>", lambda e: self._ent_reg_pass.focus())
        self._ent_reg_pass.bind("<Return>", lambda e: self._ent_reg_invite.focus())
        self._ent_reg_invite.bind("<Return>", lambda e: self._on_register_clicked())

    def _set_status(self, text: str, is_error: bool = True) -> None:
        color = _COLORS["fail"] if is_error else _COLORS["pass"]
        self._lbl_status.configure(text=text, text_color=color)

    def _on_login_clicked(self) -> None:
        username = self._ent_login_user.get().strip()
        password = self._ent_login_pass.get().strip()
        remember = bool(self._sw_remember.get())
        if not username or not password:
            self._set_status("Username and password are required.")
            return
        self._btn_login.configure(state="disabled", text="Signing in...")
        self._set_status("", False)
        def _login():
            try:
                user_data = self.handler.login_username_password(
                    username, password, remember=remember
                )
                result = {
                    "success": True,
                    "token": self.handler.session_token,
                    "user_data": user_data
                }
                self.after(0, lambda: self.on_login_success(result))
            except Exception as e:
                self.after(0, lambda: [
                    self._set_status(str(e)),
                    self._btn_login.configure(state="normal", text="Authenticate")
                ])
        threading.Thread(target=_login, daemon=True).start()

    def _on_register_clicked(self) -> None:
        username = self._ent_reg_user.get().strip()
        password = self._ent_reg_pass.get().strip()
        invite = self._ent_reg_invite.get().strip()
        if not username or not password or not invite:
            self._set_status("All fields are required for registration.")
            return
        self._btn_register.configure(state="disabled", text="Registering...")
        self._set_status("", False)
        def _register():
            try:
                user_data = self.handler.register_user(
                    username, password, invite_key=invite
                )
                result = {
                    "success": True,
                    "token": self.handler.session_token,
                    "user_data": user_data
                }
                self.after(0, lambda: self.on_login_success(result))
            except Exception as e:
                self.after(0, lambda: [
                    self._set_status(str(e)),
                    self._btn_register.configure(state="normal", text="Create Profile & Register")
                ])
        threading.Thread(target=_register, daemon=True).start()
