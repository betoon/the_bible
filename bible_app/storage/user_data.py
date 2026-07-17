"""Readers, writers, and normalizers for personal study data."""

from datetime import datetime

from bible_app.config.constants import BOOK_CHAPTERS, BOOK_ORDER
from bible_app.config.paths import (
    BOOKMARKS_PATH,
    CONCEPTS_PATH,
    HIGHLIGHTS_PATH,
    HYMN_FAVORITES_PATH,
    HYMN_LINKS_PATH,
    JOURNAL_PATH,
    NOTES_PATH,
    READING_PLANS_PATH,
    RECENT_HYMNS_PATH,
    RECENT_REFERENCES_PATH,
    STUDY_SESSIONS_PATH,
    USER_CROSS_REFERENCES_PATH,
    WORKSHEETS_PATH,
)
from bible_app.core.chapter_a_day import CHAPTER_A_DAY_PLAN_NAME, chapter_a_day_references
from bible_app.core.references import normalized_reference
from bible_app.storage.data_manager import read_json, write_json
from bible_app.storage.models import JournalEntry
from bible_app.utils.logger import get_logger


WORKSHEET_FIELDS = ["scripture", "observation", "interpretation", "application", "questions", "prayer", "related_hymn", "tags"]
logger = get_logger(__name__)


def _now():
    return datetime.now().isoformat(timespec="seconds")


def read_notes():
    return read_json(NOTES_PATH, {}, validate_notes)


def write_notes(notes):
    write_json(NOTES_PATH, validate_notes(notes))


def read_journal():
    return read_json(JOURNAL_PATH, [], normalize_journal_entries)


def write_journal(entries):
    write_json(JOURNAL_PATH, normalize_journal_entries(entries))


def read_bookmarks():
    return read_json(BOOKMARKS_PATH, [])


def write_bookmarks(bookmarks):
    write_json(BOOKMARKS_PATH, bookmarks)


def read_highlights():
    return read_json(HIGHLIGHTS_PATH, {})


def write_highlights(highlights):
    write_json(HIGHLIGHTS_PATH, highlights)


def normalize_concepts(data, default_concepts=None):
    if not isinstance(data, list):
        data = default_concepts or []
    concepts = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        concepts.append({
            "name": name,
            "category": str(item.get("category", "")),
            "summary": str(item.get("summary", "")),
            "references": [normalized_reference(ref) for ref in item.get("references", []) if isinstance(ref, str)],
            "related_readings": [str(value) for value in item.get("related_readings", []) if isinstance(value, str)],
            "notes": str(item.get("notes", "")),
            "sources": [str(value) for value in item.get("sources", []) if isinstance(value, str)],
        })
    return concepts


def read_concepts(default_concepts=None):
    return normalize_concepts(read_json(CONCEPTS_PATH, default_concepts or []), default_concepts)


def write_concepts(concepts):
    write_json(CONCEPTS_PATH, normalize_concepts(concepts))


def normalize_hymn_collection(data):
    if not isinstance(data, list):
        return []
    items = []
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        hymnal = str(item.get("hymnal", "")).strip()
        key = (hymnal, title, str(item.get("number", "")).strip())
        if not title or key in seen:
            continue
        seen.add(key)
        items.append({
            "title": title,
            "hymnal": hymnal,
            "number": str(item.get("number", "")).strip(),
            "page": int(item.get("page", 0) or 0),
            "added": str(item.get("added", _now())),
        })
    return items


def normalize_study_sessions(data):
    if not isinstance(data, list):
        return []
    sessions = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        sessions.append({
            "name": name,
            "created": str(item.get("created", _now())),
            "references": [normalized_reference(ref) for ref in item.get("references", []) if isinstance(ref, str)],
            "notes": str(item.get("notes", "")),
            "hymns": normalize_hymn_collection(item.get("hymns", [])),
            "documents": [str(value) for value in item.get("documents", []) if str(value).strip()],
        })
    return sessions


def read_study_sessions():
    return normalize_study_sessions(read_json(STUDY_SESSIONS_PATH, []))


def write_study_sessions(sessions):
    write_json(STUDY_SESSIONS_PATH, normalize_study_sessions(sessions))


def default_reading_plans():
    plans = [
        {"name": "Gospels in 30 Days", "references": [f"{book} {chapter}" for book in ("Matthew", "Mark", "Luke", "John") for chapter in range(1, BOOK_CHAPTERS[book] + 1)], "completed": []},
        {"name": "Psalms", "references": [f"Psalm {chapter}" for chapter in range(1, BOOK_CHAPTERS["Psalm"] + 1)], "completed": []},
        {"name": "New Testament Overview", "references": [f"{book} {chapter}" for book in BOOK_ORDER[39:] for chapter in range(1, BOOK_CHAPTERS[book] + 1)], "completed": []},
    ]
    chapter_a_day_refs = chapter_a_day_references()
    if chapter_a_day_refs:
        plans.insert(0, {"name": CHAPTER_A_DAY_PLAN_NAME, "references": chapter_a_day_refs, "completed": []})
    return plans


def normalize_reading_plans(data):
    if not isinstance(data, list):
        data = default_reading_plans()
    plans = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        refs = [normalized_reference(ref) if ":" in str(ref) else str(ref).strip() for ref in item.get("references", []) if str(ref).strip()]
        completed = [str(ref).strip() for ref in item.get("completed", []) if str(ref).strip()]
        plans.append({"name": name, "references": refs, "completed": completed})
    return plans


def read_reading_plans():
    plans = normalize_reading_plans(read_json(READING_PLANS_PATH, default_reading_plans()))
    existing_names = {plan["name"] for plan in plans}
    for built_in in default_reading_plans():
        if built_in["name"] not in existing_names:
            plans.append(built_in)
    return plans


def write_reading_plans(plans):
    write_json(READING_PLANS_PATH, normalize_reading_plans(plans))


def normalize_worksheets(data):
    if not isinstance(data, dict):
        return {}
    worksheets = {}
    for ref, item in data.items():
        if not isinstance(item, dict):
            continue
        worksheets[str(ref)] = {field: str(item.get(field, "")) for field in WORKSHEET_FIELDS}
        worksheets[str(ref)]["updated"] = str(item.get("updated", ""))
    return worksheets


def read_worksheets():
    return normalize_worksheets(read_json(WORKSHEETS_PATH, {}))


def write_worksheets(worksheets):
    write_json(WORKSHEETS_PATH, normalize_worksheets(worksheets))


def normalize_hymn_links(data):
    if not isinstance(data, dict):
        return {}
    links = {}
    for ref, items in data.items():
        clean_items = []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                hymnal = str(item.get("hymnal", "")).strip()
                if not title:
                    continue
                clean_items.append({
                    "title": title,
                    "hymnal": hymnal,
                    "number": str(item.get("number", "")).strip(),
                    "page": int(item.get("page", 0) or 0),
                    "linked": str(item.get("linked", _now())),
                })
        if clean_items:
            links[str(ref)] = clean_items
    return links


def read_hymn_links():
    return normalize_hymn_links(read_json(HYMN_LINKS_PATH, {}))


def write_hymn_links(links):
    write_json(HYMN_LINKS_PATH, normalize_hymn_links(links))


def read_hymn_favorites():
    return normalize_hymn_collection(read_json(HYMN_FAVORITES_PATH, []))


def write_hymn_favorites(items):
    write_json(HYMN_FAVORITES_PATH, normalize_hymn_collection(items))


def read_recent_hymns():
    return normalize_hymn_collection(read_json(RECENT_HYMNS_PATH, []))


def write_recent_hymns(items):
    write_json(RECENT_HYMNS_PATH, normalize_hymn_collection(items)[:30])


def normalize_recent_references(data):
    if not isinstance(data, list):
        return []
    items = []
    seen = set()
    for item in data:
        ref = str(item.get("reference", "") if isinstance(item, dict) else item).strip()
        if not ref or ref in seen:
            continue
        if not normalized_reference(ref):
            continue
        seen.add(ref)
        items.append({
            "reference": normalized_reference(ref),
            "opened": str(item.get("opened", _now()) if isinstance(item, dict) else _now()),
        })
    return items[:30]


def read_recent_references():
    return normalize_recent_references(read_json(RECENT_REFERENCES_PATH, []))


def write_recent_references(items):
    write_json(RECENT_REFERENCES_PATH, normalize_recent_references(items))


def normalize_user_cross_references(data):
    if not isinstance(data, dict):
        return {}
    refs = {}
    for source, items in data.items():
        clean_items = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    target = normalized_reference(item)
                    reason = "User link"
                elif isinstance(item, dict):
                    target = normalized_reference(str(item.get("target", "")))
                    reason = str(item.get("reason", "User link")).strip() or "User link"
                else:
                    continue
                if target:
                    clean_items.append({"target": target, "reason": reason})
        if clean_items:
            refs[str(source)] = clean_items
    return refs


def read_user_cross_references():
    return normalize_user_cross_references(read_json(USER_CROSS_REFERENCES_PATH, {}))


def write_user_cross_references(refs):
    write_json(USER_CROSS_REFERENCES_PATH, normalize_user_cross_references(refs))


def validate_notes(data):
    if not isinstance(data, dict):
        logger.warning("Notes data was not a dictionary; using empty notes.")
        return {}
    notes = {}
    for ref, text in data.items():
        clean_ref = normalized_reference(str(ref))
        clean_text = str(text).strip()
        if clean_ref and clean_text:
            notes[clean_ref] = clean_text
    return notes


def normalize_journal_entries(data):
    if not isinstance(data, list):
        logger.warning("Journal data was not a list; using empty journal.")
        return []
    entries = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            entry = JournalEntry(
                reference=str(item.get("reference", "")),
                verse=str(item.get("verse", "")),
                reflection=str(item.get("reflection", "")),
                prayer=str(item.get("prayer", "")),
                images=[str(path) for path in item.get("images", []) if str(path).strip()],
                created=str(item.get("created", _now())),
            )
            entries.append(entry.to_dict())
        except ValueError as exc:
            logger.warning("Skipping invalid journal entry: %s", exc)
    return entries
