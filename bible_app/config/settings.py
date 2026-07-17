"""INI-backed application settings with safe defaults."""

import os
from configparser import ConfigParser
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("settings.ini")


DEFAULTS = {
    "app": {
        "app_title": "Bible Reference Study Tool - Windows 11 Edition",
        "header_title": "Bible Reference Study Tool",
        "window_width": "1260",
        "window_height": "780",
        "min_width": "980",
        "min_height": "640",
        "theme": "light",
    },
    "api": {
        "bible_api_url": "https://bible-api.com/{reference}?translation=kjv",
        "jps_base_url": "https://www.mechon-mamre.org/e/et/{code}{chapter:02d}.htm",
        "timeout": "20",
        "retry_attempts": "3",
        "connection_check_timeout": "8",
    },
    "translations": {
        "default": "KJV",
        "online": "KJV,JPS1917",
    },
    "storage": {
        "max_backups": "10",
        "auto_backup_on_startup": "true",
    },
    "performance": {
        "background_workers": "3",
        "passage_cache_size": "1024",
    },
    "ui": {
        "app_bg": "#F3F3F3",
        "app_panel": "#FFFFFF",
        "accent": "#0078D4",
        "text": "#1F1F1F",
        "text_secondary": "#616161",
        "border": "#E0E0E0",
    },
    "reader": {
        "reader_bg": "#fbfcfd",
        "reader_fg": "#1F1F1F",
        "highlight_bg": "#edf6f5",
        "reader_font": "Georgia",
        "reader_font_size": "13",
        "show_strongs": "true",
    },
    "windows": {
        "study_dashboard": "760x640",
        "journal": "760x680",
        "passage_worksheet": "780x760",
        "reading_plans": "820x640",
        "chapter_a_day": "1200x820",
        "study_sessions": "860x620",
        "study_binder": "900x700",
        "hymnal_viewer": "980x720",
        "hymn_list": "520x420",
        "library_manager": "720x620",
        "document_converter": "560x260",
        "document_viewer": "900x700",
        "web_commentary_importer": "760x520",
        "search_everything": "820x640",
        "timeline": "820x620",
        "map_viewer": "980x760",
        "people_explorer": "860x680",
        "person_profile": "760x820",
        "concept_library": "960x680",
        "cross_reference_explorer": "760x620",
        "cross_reference_graph": "760x560",
        "presentation_mode": "1000x720",
        "settings": "520x750",
        "help": "820x640",
    },
    "window_minimums": {
        "study_dashboard": "640x480",
        "journal": "620x520",
        "passage_worksheet": "640x560",
        "reading_plans": "640x440",
        "chapter_a_day": "900x640",
        "study_sessions": "700x480",
        "study_binder": "740x520",
        "hymnal_viewer": "780x540",
        "hymn_list": "420x320",
        "library_manager": "600x480",
        "document_converter": "480x240",
        "document_viewer": "700x520",
        "web_commentary_importer": "620x420",
        "search_everything": "680x500",
        "timeline": "680x500",
        "map_viewer": "720x520",
        "people_explorer": "720x540",
        "person_profile": "620x580",
        "concept_library": "760x540",
        "cross_reference_explorer": "620x460",
        "cross_reference_graph": "620x420",
        "presentation_mode": "800x560",
        "settings": "480x700",
        "help": "680x500",
    },
}


class Settings:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config = ConfigParser()
        self.config.read_dict(DEFAULTS)
        self.config.read(self.config_path, encoding="utf-8")

    def get(self, section, option):
        env_key = f"BIBLE_APP_{section}_{option}".upper()
        if env_key in os.environ:
            return os.environ[env_key]
        return self.config.get(section, option)

    def getint(self, section, option):
        try:
            return int(self.get(section, option))
        except (TypeError, ValueError):
            return int(DEFAULTS[section][option])

    def getbool(self, section, option):
        value = str(self.get(section, option)).strip().lower()
        return value in {"1", "yes", "true", "on"}

    def getlist(self, section, option):
        return [item.strip() for item in self.get(section, option).split(",") if item.strip()]

    def get_window_geometry(self, key, fallback):
        return self._validated_geometry("windows", key, fallback)

    def get_window_minsize(self, key, fallback):
        value = self._validated_geometry("window_minimums", key, fallback)
        width, height = value.lower().split("x", 1)
        return int(width), int(height)

    def _validated_geometry(self, section, option, fallback):
        if not self.config.has_option(section, option):
            return fallback
        value = str(self.get(section, option)).strip().lower()
        if not value:
            return fallback
        parts = value.split("x", 1)
        if len(parts) != 2:
            return fallback
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError:
            return fallback
        if width < 240 or height < 180:
            return fallback
        return f"{width}x{height}"

    @property
    def app_title(self):
        return self.get("app", "app_title")

    @property
    def header_title(self):
        return self.get("app", "header_title")

    @property
    def window_geometry(self):
        return f"{self.getint('app', 'window_width')}x{self.getint('app', 'window_height')}"

    @property
    def min_window_size(self):
        return self.getint("app", "min_width"), self.getint("app", "min_height")

    @property
    def default_translation(self):
        return self.get("translations", "default")

    @property
    def online_translations(self):
        return self.getlist("translations", "online")

    @property
    def max_backups(self):
        return self.getint("storage", "max_backups")

    @property
    def auto_backup_on_startup(self):
        return self.getbool("storage", "auto_backup_on_startup")

    @property
    def background_workers(self):
        return self.getint("performance", "background_workers")

    @property
    def passage_cache_size(self):
        return self.getint("performance", "passage_cache_size")


APP_SETTINGS = Settings()

APP_BG = APP_SETTINGS.get("ui", "app_bg")
APP_PANEL = APP_SETTINGS.get("ui", "app_panel")
ACCENT = APP_SETTINGS.get("ui", "accent")
TEXT = APP_SETTINGS.get("ui", "text")
TEXT_SECONDARY = APP_SETTINGS.get("ui", "text_secondary")
BORDER = APP_SETTINGS.get("ui", "border")
BIBLE_API_URL = APP_SETTINGS.get("api", "bible_api_url")
JPS_BASE_URL = APP_SETTINGS.get("api", "jps_base_url")
API_TIMEOUT = APP_SETTINGS.getint("api", "timeout")
API_RETRY_ATTEMPTS = APP_SETTINGS.getint("api", "retry_attempts")
CONNECTION_CHECK_TIMEOUT = APP_SETTINGS.getint("api", "connection_check_timeout")
DEFAULT_TRANSLATION = APP_SETTINGS.default_translation
ONLINE_TRANSLATIONS = APP_SETTINGS.online_translations
MAX_BACKUPS = APP_SETTINGS.max_backups
AUTO_BACKUP_ON_STARTUP = APP_SETTINGS.auto_backup_on_startup
BACKGROUND_WORKERS = APP_SETTINGS.background_workers
PASSAGE_CACHE_SIZE = APP_SETTINGS.passage_cache_size

TRANSLATION_LABELS = {
    "KJV": "King James Version",
    "JPS1917": "JPS 1917 Hebrew Bible / Tanakh",
    "NIV": "New International Version",
    "ESV": "English Standard Version",
}

DEFAULT_READER_SETTINGS = {
    "reader_bg": APP_SETTINGS.get("reader", "reader_bg"),
    "reader_fg": APP_SETTINGS.get("reader", "reader_fg"),
    "highlight_bg": APP_SETTINGS.get("reader", "highlight_bg"),
    "reader_font": APP_SETTINGS.get("reader", "reader_font"),
    "reader_font_size": APP_SETTINGS.getint("reader", "reader_font_size"),
    "show_strongs": APP_SETTINGS.getbool("reader", "show_strongs"),
}
