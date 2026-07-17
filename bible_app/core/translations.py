"""Bible translation normalization and formatting helpers."""

import re

from bible_app.config.paths import BUNDLED_ENGLISH_DIR, BUNDLED_TRANSLATION_CACHE_PATH
from bible_app.core.references import canonical_book_name
from bible_app.storage.data_manager import read_json, write_json
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


WEB_NOISE_MARKERS = (
    "__CF$cv",
    "challenge-platform",
    "cdn-cgi",
    "document.createElement",
    "appendChild",
    "contentDocument",
    "contentWindow",
    "chapters(",
)


def bible_text_has_web_noise(value):
    text = str(value or "")
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in WEB_NOISE_MARKERS):
        return True
    return "'et" in lowered and 'copy("")' in lowered and bool(
        re.search(r"'et\d+'\s*,.*copy\(\"\"\)", text, flags=re.I | re.S)
    )


def clean_bible_verse_text(value):
    """Remove web page script leftovers from cached or imported verse text."""
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if "window.__cf$cv" in lowered:
        text = re.sub(r"\s*window\.__CF\$cv.*$", "", text, flags=re.I | re.S)
        lowered = text.lower()
    if "(function()" in lowered:
        text = re.sub(r"\s*\(function\(\).*?$", "", text, flags=re.I | re.S)
        lowered = text.lower()
    if 'copy("")' in lowered:
        text = re.sub(r"\s*copy\(\"\"\).*$", "", text, flags=re.I | re.S)
        lowered = text.lower()
    if "'et" in lowered:
        text = re.sub(r"\s*,?\s*'et\d+'\s*,.*$", "", text, flags=re.I | re.S)
        lowered = text.lower()
    if "chapters(" in lowered:
        text = re.sub(r"\s+chapters\([^)]*$", "", text, flags=re.I | re.S)
    if bible_text_has_web_noise(text):
        logger.warning("Dropped verse text containing web page script noise.")
        return ""
    return " ".join(text.split())


def normalize_bible_data(data):
    normalized = {}
    if not isinstance(data, dict):
        return normalized
    for translation, books in data.items():
        if not isinstance(books, dict):
            continue
        normalized[translation] = {}
        for book, chapters in books.items():
            if not isinstance(chapters, dict):
                continue
            normalized[translation][book] = {}
            for chapter, verses in chapters.items():
                try:
                    chapter_number = int(chapter)
                except Exception as exc:
                    logger.debug("Skipping invalid chapter key in %s %s: %s", translation, book, exc)
                    continue
                if isinstance(verses, list):
                    cleaned_verses = [clean_bible_verse_text(verse) for verse in verses]
                    while cleaned_verses and not cleaned_verses[-1]:
                        cleaned_verses.pop()
                    normalized[translation][book][chapter_number] = cleaned_verses
    return normalized


def bundled_translation_code(metadata, fallback):
    raw = str(metadata.get("shortname") or fallback).strip()
    code = re.sub(r"[^A-Za-z0-9]+", "", raw).upper()
    if code == "KJV":
        return "KJV"
    return code or fallback.upper()


def normalize_bundled_bible_file(path):
    payload = read_json(path, {})
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    verses = payload.get("verses", []) if isinstance(payload, dict) else []
    if not isinstance(metadata, dict) or not isinstance(verses, list):
        return None, None, {}
    if metadata.get("restrict", 1):
        return None, None, {}
    code = bundled_translation_code(metadata, path.stem)
    label = str(metadata.get("name") or metadata.get("shortname") or path.stem)
    translation = {}
    for item in verses:
        if not isinstance(item, dict):
            continue
        book = canonical_book_name(item.get("book_name", ""))
        if not book:
            continue
        try:
            chapter = int(item.get("chapter"))
            verse = int(item.get("verse"))
        except Exception as exc:
            logger.debug("Skipping bundled verse with invalid chapter/verse in %s: %s", path, exc)
            continue
        text = clean_bible_verse_text(item.get("text", ""))
        if not text:
            continue
        chapter_verses = translation.setdefault(book, {}).setdefault(chapter, [])
        while len(chapter_verses) < verse:
            chapter_verses.append("")
        chapter_verses[verse - 1] = text
    return code, label, translation


def bundled_translation_sources(directory):
    """Return source files and metadata used to validate the normalized cache."""
    paths = sorted(directory.glob("*.json"))
    metadata = []
    for path in paths:
        try:
            stat = path.stat()
        except OSError as exc:
            logger.debug("Could not stat bundled translation %s: %s", path, exc)
            continue
        metadata.append({
            "path": str(path.resolve()),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        })
    return paths, metadata


def restore_cached_translations(data):
    """Restore cached translation chapter keys from JSON strings to integers."""
    restored = {}
    if not isinstance(data, dict):
        return restored
    for code, books in data.items():
        if not isinstance(books, dict):
            continue
        restored[code] = {}
        for book, chapters in books.items():
            if not isinstance(chapters, dict):
                continue
            restored[code][book] = {}
            for chapter, verses in chapters.items():
                try:
                    chapter_number = int(chapter)
                except Exception:
                    continue
                if isinstance(verses, list):
                    restored[code][book][chapter_number] = verses
    return restored


def load_bundled_translations(directory=BUNDLED_ENGLISH_DIR):
    translations = {}
    labels = {}
    if not directory.exists():
        return translations, labels
    paths, metadata = bundled_translation_sources(directory)
    cache = read_json(BUNDLED_TRANSLATION_CACHE_PATH, {})
    if (
        isinstance(cache, dict)
        and cache.get("directory") == str(directory.resolve())
        and cache.get("sources") == metadata
        and isinstance(cache.get("translations"), dict)
        and isinstance(cache.get("labels"), dict)
    ):
        logger.info("Loaded bundled translations from normalized cache.")
        return restore_cached_translations(cache["translations"]), cache["labels"]

    for path in paths:
        code, label, translation = normalize_bundled_bible_file(path)
        if code and translation:
            translations[code] = translation
            labels[code] = label
    if translations:
        try:
            write_json(
                BUNDLED_TRANSLATION_CACHE_PATH,
                {
                    "directory": str(directory.resolve()),
                    "sources": metadata,
                    "translations": translations,
                    "labels": labels,
                },
                make_backup=False,
            )
        except Exception as exc:
            logger.debug("Could not write bundled translation cache: %s", exc)
    return translations, labels


def bundled_translation_for(code, directory=BUNDLED_ENGLISH_DIR):
    translations, labels = load_bundled_translations(directory)
    key = str(code).upper()
    return translations.get(key), labels.get(key, key)


def niv_chapter_segments(text):
    text = str(text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<!\d)(\d{1,3})(?=[A-Za-z\"'(\u201c])", text)
    segments = []
    first = parts[0].strip()
    if first:
        segments.append((1, first))
    for index in range(1, len(parts), 2):
        try:
            verse_number = int(parts[index])
        except Exception as exc:
            logger.debug("Skipping invalid NIV verse marker %r: %s", parts[index], exc)
            continue
        verse_text = parts[index + 1].strip() if index + 1 < len(parts) else ""
        if verse_text:
            segments.append((verse_number, verse_text))
    if not segments:
        return [(1, text)]
    return segments


def format_niv_chapter_text(text):
    return "\n\n".join(f"{number}. {verse}" for number, verse in niv_chapter_segments(text))
