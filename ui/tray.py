import logging
import threading
from PIL import Image, ImageDraw
import pystray

logger = logging.getLogger("TrayIcon")

class StealthTray:
    def __init__(self, on_show_dashboard, on_show_settings, on_show_license, on_restart_engine, on_exit_app):
        self.on_show_dashboard = on_show_dashboard
        self.on_show_settings = on_show_settings
        self.on_show_license = on_show_license
        self.on_restart_engine = on_restart_engine
        self.on_exit_app = on_exit_app
        self.icon = None
        self.running = False
        self.status_message = "Listening"

    def create_dynamic_icon(self) -> Image.Image:
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=None, outline=(48, 209, 88, 100), width=4)
        draw.ellipse([16, 16, 48, 48], fill=(48, 209, 88, 255))
        draw.ellipse([24, 24, 40, 40], fill=(255, 255, 255, 255))
        return image

    def setup_tray(self):
        self.rebuild_menu()
        img = self.create_dynamic_icon()
        self.icon = pystray.Icon(
            "portal_client",
            icon=img,
            title="NovaGhost",
            menu=self.current_menu
        )
        logger.info("Starting system tray loop...")
        self.icon.run()

    def rebuild_menu(self):
        self.current_menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", lambda: self.on_show_dashboard()),
            pystray.MenuItem("Open Settings", lambda: self.on_show_settings()),
            pystray.MenuItem("License Information", lambda: self.on_show_license()),
            pystray.MenuItem(f"Status: {self.status_message}", lambda: None, enabled=False),
            pystray.MenuItem("Restart Engine", lambda: self.on_restart_engine()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit System", lambda: self.handle_exit())
        )
        if self.icon:
            self.icon.menu = self.current_menu

    def update_status(self, new_status: str):
        self.status_message = new_status
        self.rebuild_menu()

    def start(self):
        if self.running:
            return
        self.running = True
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True, name="TrayDaemon")
        self.tray_thread.start()

    def stop(self):
        self.running = False
        if self.icon:
            self.icon.stop()
            logger.info("System tray icon stopped.")

    def handle_exit(self):
        logger.warning("System tray 'Exit' clicked. Initiating termination.")
        self.stop()
        self.on_exit_app()
