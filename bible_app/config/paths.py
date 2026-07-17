"""Filesystem paths for source, bundled resources, and user data."""

import os
import sys
from pathlib import Path


APP_DIR = Path(os.environ.get("BIBLE_APP_APP_DIR", Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]))
RESOURCE_DIR = Path(os.environ.get("BIBLE_APP_RESOURCE_DIR", getattr(sys, "_MEIPASS", APP_DIR)))


def default_user_data_dir():
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "BibleReferenceStudyTool"


USER_DATA_DIR = Path(os.environ.get("BIBLE_APP_USER_DATA_DIR", default_user_data_dir()))
DATA_DIR = USER_DATA_DIR / "data"
APP_DATA_DIR = Path(os.environ.get("BIBLE_APP_DATA_DIR", RESOURCE_DIR / "data"))
BUNDLED_ENGLISH_DIR = APP_DATA_DIR / "EN-English"
BIBLE_DATA_PATH = DATA_DIR / "kjv_bible.json"
BUNDLED_TRANSLATION_CACHE_PATH = DATA_DIR / "bundled_translations_cache.json"
NOTES_PATH = USER_DATA_DIR / "bible_personal_notes.json"
JOURNAL_PATH = USER_DATA_DIR / "bible_private_journal.json"
BOOKMARKS_PATH = USER_DATA_DIR / "bible_bookmarks.json"
HIGHLIGHTS_PATH = USER_DATA_DIR / "bible_highlights.json"
CONCEPTS_PATH = USER_DATA_DIR / "bible_concepts.json"
STUDY_SESSIONS_PATH = USER_DATA_DIR / "bible_study_sessions.json"
READING_PLANS_PATH = USER_DATA_DIR / "bible_reading_plans.json"
WORKSHEETS_PATH = USER_DATA_DIR / "bible_study_worksheets.json"
HYMN_LINKS_PATH = USER_DATA_DIR / "bible_hymn_links.json"
HYMN_FAVORITES_PATH = USER_DATA_DIR / "bible_hymn_favorites.json"
RECENT_HYMNS_PATH = USER_DATA_DIR / "bible_recent_hymns.json"
RECENT_REFERENCES_PATH = USER_DATA_DIR / "bible_recent_references.json"
USER_CROSS_REFERENCES_PATH = USER_DATA_DIR / "bible_user_cross_references.json"
SETTINGS_PATH = USER_DATA_DIR / "bible_settings.json"
BACKUP_DIR = USER_DATA_DIR / "backups"
EXPORT_DIR = USER_DATA_DIR / "exports"
COMMENTARY_DIR = USER_DATA_DIR / "commentary"
DOCUMENT_LIBRARY_DIR = USER_DATA_DIR / "documents"
DOCUMENT_LIBRARY_PATH = DOCUMENT_LIBRARY_DIR / "library.json"
DOCUMENT_IMAGE_DIR = DOCUMENT_LIBRARY_DIR / "images"
HYMNAL_INDEX_CACHE_PATH = USER_DATA_DIR / "hymnal_index_cache.json"
STUDY_DATA_DIR = RESOURCE_DIR / "study_data"
STUDY_DATA_PATH = STUDY_DATA_DIR / "study_notes.json"
THEMES_DATA_PATH = STUDY_DATA_DIR / "themes.json"
PEOPLE_DATA_PATH = STUDY_DATA_DIR / "people.json"
PEOPLE_REFERENCE_PATH = STUDY_DATA_DIR / "people_reference.json"
MAPS_DATA_PATH = STUDY_DATA_DIR / "maps.json"
CHAPTER_A_DAY_PATH = STUDY_DATA_DIR / "chapter_a_day_2026.json"
MAPS_DIR = RESOURCE_DIR / "maps"
PEOPLE_TEXT_DIR = APP_DATA_DIR / "people"
MAPS_ASSET_DIR = APP_DATA_DIR / "maps"
NIV_PDF_PATH = APP_DATA_DIR / "NIV-Bible.pdf"
HYMNALS_DIR = APP_DATA_DIR / "hymnals"
