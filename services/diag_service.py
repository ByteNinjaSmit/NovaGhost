import os
import sys
import platform
import shutil
import ctypes
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from config import config
from utils.log import log_exception

def scrub_sensitive_info(text: str) -> str:
    if not text:
        return text
    for provider, key in config.API_KEYS.items():
        if key and key != "local":
            text = text.replace(key, f"[REDACTED_{provider.upper()}_KEY]")
    return text

logger = logging.getLogger("DiagnosticsService")

@dataclass
class PhaseResult:
    phase: str
    status: str
    message: str = ""
    error: str = ""
    module: str = ""
    function: str = ""
    traceback_str: str = ""

@dataclass
class DiagnosticReport:
    version: str
    timestamp: str
    overall: str = "pass"
    phases: list = field(default_factory=list)
    safe_mode: bool = False

    def add(self, result: PhaseResult) -> None:
        self.phases.append(result)
        if result.status == "fail":
            self.overall = "fail"

    def get_failures(self) -> list:
        return [p for p in self.phases if p.status == "fail"]

    def get_warnings(self) -> list:
        return [p for p in self.phases if p.status == "warn"]

class DiagnosticsService:
    def __init__(self, auth_handler=None, session_token: str = ""):
        self.auth_handler = auth_handler
        self.session_token = session_token
        self._progress_callback = None

    def set_progress_callback(self, callback) -> None:
        self._progress_callback = callback

    def _report_progress(self, phase: str, status: str, message: str = "") -> None:
        if self._progress_callback:
            try:
                self._progress_callback(phase, status, message)
            except Exception:
                pass

    def run(self, safe_mode: bool = False) -> DiagnosticReport:
        report = DiagnosticReport(
            version=config.CURRENT_VERSION,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            safe_mode=safe_mode
        )
        self._report_progress("Diagnostic", "running", "Starting full system test...")
        self._phase_startup(report)
        self._phase_api_config(report)
        self._phase_dependencies(report)
        self._phase_capture(report)
        if not safe_mode:
            self._phase_gesture(report)
            self._phase_ai_pipeline(report)
            self._phase_overlay(report)
        else:
            report.add(PhaseResult("Gesture System", "skip", "Skipped in safe mode."))
            report.add(PhaseResult("AI Pipeline", "skip", "Skipped in safe mode."))
            report.add(PhaseResult("Overlay System", "skip", "Skipped in safe mode."))
        return report

    def _phase_startup(self, report: DiagnosticReport) -> None:
        phase = "Startup"
        self._report_progress(phase, "running")
        checks = []
        try:
            _ = config.CURRENT_VERSION
            checks.append("Configuration loaded")
        except Exception as e:
            report.add(PhaseResult(phase, "fail", error=str(e), module="Config", function="load", traceback_str=traceback.format_exc()))
            return
        try:
            if config.SETTINGS_FILE.exists():
                import json
                with open(config.SETTINGS_FILE, "r", encoding="utf-8-sig") as f:
                    json.load(f)
            checks.append("Settings file valid")
        except Exception as e:
            report.add(PhaseResult(phase, "warn", message=f"Settings file issue: {e}", module="Config", function="load"))
            return
        try:
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            test_file = config.LOG_DIR / ".write_test"
            test_file.write_text("ok")
            test_file.unlink()
            checks.append("Log directory writable")
        except Exception as e:
            report.add(PhaseResult(phase, "fail", message="Log directory not writable", error=str(e), module="Config", function="init", traceback_str=traceback.format_exc()))
            return
        report.add(PhaseResult(phase, "pass", message='; '.join(checks)))
        self._report_progress(phase, "pass", "All startup checks passed")

    def _phase_api_config(self, report: DiagnosticReport) -> None:
        phase = "API Configuration"
        self._report_progress(phase, "running")
        provider = config.ACTIVE_PROVIDER
        if config.has_primary_key():
            msg = f"Active provider '{provider}' | Model: {config.ACTIVE_MODEL}"
            if config.FALLBACK_ENABLED:
                fb_ok = "key set" if config.has_fallback_key() else "no key"
                msg += f" | Fallback: {config.FALLBACK_PROVIDER} ({fb_ok})"
            report.add(PhaseResult(phase, "pass", message=msg))
            self._report_progress(phase, "pass", "API key configured")
        else:
            report.add(PhaseResult(
                phase, "warn",
                message=f"No API key set for active provider '{provider}'. "
                        "Open Preferences and enter your API key.",
                module="Config", function="has_primary_key"
            ))
            self._report_progress(phase, "warn", "No API key set")

    def _phase_dependencies(self, report: DiagnosticReport) -> None:
        phase = "Dependencies"
        self._report_progress(phase, "running")
        issues = []
        try:
            from services.env_service import EnvService
            libs = EnvService.verify_python_libs()
            for lib, ok in libs.items():
                if not ok:
                    issues.append(f"Library missing: {lib}")
        except Exception as e:
            issues.append(f"Library check error: {e}")
        py_info = f"Python {platform.python_version()} ({platform.architecture()[0]})"
        dpi_info = _get_dpi_info()
        if issues:
            report.add(PhaseResult(phase, "fail", message=f"Issues: {'; '.join(issues)}", error='; '.join(issues), module="EnvService", function="check"))
            self._report_progress(phase, "fail", issues[0])
        else:
            msg = f"Runtime: {py_info} | DPI: {dpi_info} | Core Libraries: OK"
            report.add(PhaseResult(phase, "pass", message=msg))
            self._report_progress(phase, "pass", "Dependencies verified")

    def _phase_capture(self, report: DiagnosticReport) -> None:
        phase = "Capture System"
        self._report_progress(phase, "running")
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            w, h = screenshot.size
            if w <= 0 or h <= 0:
                raise ValueError(f"Invalid dimensions: {w}x{h}")
            region_msg = "Full screen"
            if config.CROP_BOX:
                x1, y1, x2, y2 = config.CROP_BOX
                if (0 <= x1 < x2 <= w) and (0 <= y1 < y2 <= h):
                    region_msg = f"Custom region {config.CROP_BOX}"
                else:
                    report.add(PhaseResult(phase, "warn", message="Capture region is out of bounds."))
                    return
            report.add(PhaseResult(phase, "pass", message=f"Capture OK ({w}x{h}) | Region: {region_msg}"))
            self._report_progress(phase, "pass", f"Screen {w}x{h} captured")
        except Exception as e:
            report.add(PhaseResult(phase, "fail", message="Screen capture failed", error=str(e), module="ScreenCaptureManager", function="capture_screen", traceback_str=traceback.format_exc()))
            self._report_progress(phase, "fail", f"Capture failed: {e}")

    def _phase_gesture(self, report: DiagnosticReport) -> None:
        phase = "Gesture System"
        self._report_progress(phase, "running")
        try:
            from pynput import mouse
            _ = mouse.Listener
            report.add(PhaseResult(phase, "pass", message=f"Input detection ready | Window: {config.TRIPLE_TAP_WINDOW}s"))
            self._report_progress(phase, "pass", "Gesture system ready")
        except ImportError as e:
            report.add(PhaseResult(phase, "fail", message="Input library missing", error=str(e), module="InputDetector", function="start", traceback_str=traceback.format_exc()))
        except Exception as e:
            report.add(PhaseResult(phase, "fail", message="Gesture check failed", error=str(e), module="InputDetector", function="start", traceback_str=traceback.format_exc()))

    def _phase_ai_pipeline(self, report: DiagnosticReport) -> None:
        phase = "AI Pipeline"
        self._report_progress(phase, "running")
        has_primary = config.has_primary_key()
        has_fallback = config.has_fallback_key()
        if not has_primary and not has_fallback:
            report.add(PhaseResult(phase, "fail", message="No AI keys configured.", module="ApiClient", function="query"))
            return
        try:
            import requests
            if has_primary:
                if config.ACTIVE_PROVIDER == "gemini":
                    res = requests.get("https://generativelanguage.googleapis.com", timeout=5)
                elif config.ACTIVE_PROVIDER == "openrouter":
                    res = requests.get("https://openrouter.ai", timeout=5)
                else:
                    res = requests.get("https://api.openai.com", timeout=5)
                
                if res.status_code in [200, 403, 400, 404, 401]:
                    report.add(PhaseResult(phase, "pass", message=f"Active provider endpoint ({config.ACTIVE_PROVIDER}) reachable."))
                    self._report_progress(phase, "pass", "AI Endpoint reachable")
                    return
            if has_fallback:
                fb_prov = config.FALLBACK_PROVIDER
                if fb_prov == "openrouter":
                    res = requests.get("https://openrouter.ai", timeout=5)
                elif fb_prov == "gemini":
                    res = requests.get("https://generativelanguage.googleapis.com", timeout=5)
                else:
                    res = requests.get("https://api.openai.com", timeout=5)
                
                if res.status_code in [200, 403, 400, 404, 401]:
                    report.add(PhaseResult(phase, "pass", message=f"Fallback provider endpoint ({fb_prov}) reachable."))
                    self._report_progress(phase, "pass", "AI Endpoint (fallback) reachable")
                    return
            report.add(PhaseResult(phase, "fail", message="AI Endpoint unreachable", module="ApiClient", function="query"))
        except Exception as e:
            report.add(PhaseResult(phase, "fail", message="AI pipeline connection failed", error=str(e), module="ApiClient", function="query", traceback_str=traceback.format_exc()))

    def _phase_overlay(self, report: DiagnosticReport) -> None:
        phase = "Overlay System"
        self._report_progress(phase, "running")
        try:
            import tkinter as tk
            root_exists = tk._default_root is not None
            if root_exists:
                test_win = tk.Toplevel(tk._default_root)
                test_win.withdraw()
                test_win.update_idletasks()
                test_win.destroy()
                report.add(PhaseResult(phase, "pass", message="Overlay verified."))
            else:
                report.add(PhaseResult(phase, "pass", message="Overlay available."))
            self._report_progress(phase, "pass", "Overlay system ready")
        except Exception as e:
            report.add(PhaseResult(phase, "fail", message="Overlay verification failed", error=str(e), module="OverlayController", function="_show_overlay", traceback_str=traceback.format_exc()))

    def write_test_log(self, report: DiagnosticReport) -> Path:
        try:
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            content = self._format_report(report)
            with open(config.TEST_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            return config.TEST_LOG_FILE
        except Exception as e:
            log_exception(logger, "DiagnosticsService", "write_test_log", e)
            return config.TEST_LOG_FILE

    def _format_report(self, report: DiagnosticReport) -> str:
        lines = []
        lines.append("=" * 68)
        lines.append("               SYSTEM DIAGNOSTIC REPORT")
        lines.append(f"           Version: {report.version}")
        lines.append(f"           Generated: {report.timestamp}")
        if report.safe_mode:
            lines.append("           Mode: SAFE MODE")
        lines.append("=" * 68)
        lines.append("")
        status_icons = {"pass": "✓ PASS", "fail": "✗ FAIL", "warn": "⚠ WARN", "skip": "○ SKIP"}
        for p in report.phases:
            icon = status_icons.get(p.status, "? UNKN")
            lines.append(f"[{icon}] {p.phase}")
            if p.message:
                lines.append(f"        {p.message}")
            lines.append("")
        lines.append("=" * 68)
        lines.append(f"  OVERALL RESULT: {'PASS ✓' if report.overall == 'pass' else 'FAIL ✗'}")
        lines.append("=" * 68)
        failures = report.get_failures()
        if failures:
            lines.append("")
            lines.append("FAILURE DETAILS:")
            lines.append("-" * 68)
            for p in failures:
                lines.append(f"  Phase:     {p.phase}")
                if p.module:
                    lines.append(f"  Module:    {p.module}")
                if p.function:
                    lines.append(f"  Function:  {p.function}")
                lines.append(f"  Error:     {p.error or p.message}")
                if p.traceback_str and p.traceback_str.strip() not in ["", "NoneType: None"]:
                    lines.append(f"  Traceback:")
                    for tb_line in p.traceback_str.strip().split("\n"):
                        lines.append(f"    {tb_line}")
                lines.append("")
        warnings = report.get_warnings()
        if warnings:
            lines.append("WARNINGS:")
            lines.append("-" * 68)
            for p in warnings:
                lines.append(f"  ⚠ {p.phase}: {p.message}")
            lines.append("")
        lines.append("=" * 68)
        lines.append("                  END OF REPORT")
        lines.append("=" * 68)
        return scrub_sensitive_info("\n".join(lines))

    def get_report_text(self, report: DiagnosticReport) -> str:
        return self._format_report(report)

def _get_dpi_info() -> str:
    if sys.platform != "win32":
        return "N/A"
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        hdc = ctypes.windll.user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        scale = (dpi_x / 96.0) * 100
        return f"{scale:.0f}% (DPI: {dpi_x})"
    except Exception:
        return "Unknown"

DiagnosticsService = DiagnosticsService
