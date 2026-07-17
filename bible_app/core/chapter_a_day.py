"""Chapter A Day reading plan helpers."""

from bible_app.config.paths import CHAPTER_A_DAY_PATH
from bible_app.core.references import normalized_reference
from bible_app.storage.data_manager import read_json


CHAPTER_A_DAY_PLAN_NAME = "Chapter A Day 2026"


def load_chapter_a_day_data():
    """Load the extracted Chapter A Day schedule."""
    data = read_json(CHAPTER_A_DAY_PATH, {})
    entries = []
    if isinstance(data, dict):
        for item in data.get("entries", []):
            if not isinstance(item, dict):
                continue
            try:
                day = int(item.get("day"))
            except Exception:
                continue
            reference = str(item.get("reference", "")).strip()
            if not day or not reference:
                continue
            entries.append({
                "day": day,
                "reference": normalized_reference(reference) if ":" in reference else reference,
                "page": int(item.get("page", 0) or 0),
            })
    entries.sort(key=lambda item: item["day"])
    return {
        "name": str(data.get("name") or CHAPTER_A_DAY_PLAN_NAME) if isinstance(data, dict) else CHAPTER_A_DAY_PLAN_NAME,
        "description": str(data.get("description", "")) if isinstance(data, dict) else "",
        "entries": entries,
    }


def chapter_a_day_references():
    """Return the 365 chapter references for the reading-plan list."""
    return [entry["reference"] for entry in load_chapter_a_day_data().get("entries", [])]


def chapter_a_day_entry_for_index(index):
    """Return the day entry for a zero-based list index."""
    entries = load_chapter_a_day_data().get("entries", [])
    if 0 <= index < len(entries):
        return entries[index]
    return None


def is_chapter_a_day_plan_name(name):
    """True when a reading plan is the built-in Chapter A Day plan."""
    return str(name or "").strip().lower() == CHAPTER_A_DAY_PLAN_NAME.lower()
