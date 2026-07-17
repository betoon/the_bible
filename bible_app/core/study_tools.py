"""Themes, people, concepts, and study-data normalization helpers."""

import re
from pathlib import Path

from bible_app.config.constants import BOOK_CHAPTERS
from bible_app.config.paths import PEOPLE_TEXT_DIR
from bible_app.core.references import canonical_book_name, normalized_reference


def normalize_study_data(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for ref, entry in data.items():
        if not isinstance(entry, dict):
            continue
        language = []
        for item in entry.get("language", []):
            if isinstance(item, dict):
                language.append((item.get("word", ""), item.get("original", ""), item.get("note", "")))
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                language.append((item[0], item[1], item[2]))
        normalized[ref] = {
            "teaching": str(entry.get("teaching", "")),
            "cross": [str(cross_ref) for cross_ref in entry.get("cross", []) if isinstance(cross_ref, str)],
            "language": language,
            "map": str(entry.get("map", "")),
            "people": [str(item) for item in entry.get("people", []) if isinstance(item, str)],
            "places": [str(item) for item in entry.get("places", []) if isinstance(item, str)],
            "timeline": str(entry.get("timeline", "")),
        }
    return normalized


def normalize_people_data(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for name, entry in data.items():
        if not isinstance(entry, dict):
            continue
        normalized[str(name)] = {
            "canon": str(entry.get("canon", "")),
            "category": str(entry.get("category", "")),
            "roles": [str(item) for item in entry.get("roles", []) if isinstance(item, str)],
            "summary": str(entry.get("summary", "")),
            "references": [normalized_reference(item) for item in entry.get("references", []) if isinstance(item, str)],
            "related_people": [str(item) for item in entry.get("related_people", []) if isinstance(item, str)],
            "aliases": [str(item) for item in entry.get("aliases", []) if isinstance(item, str)],
            "article": str(entry.get("article", "")),
            "source": str(entry.get("source", "")),
        }
    return normalized


def clean_imported_text(text):
    replacements = {
        "Ã¢â‚¬â„¢": "'",
        "Ã¢â‚¬Å“": '"',
        "Ã¢â‚¬ï¿½": '"',
        "Ã¢â‚¬Ëœ": "'",
        "Ã¢â‚¬â€œ": "-",
        "Ã¢â‚¬â€": "-",
        "Ã¢â€ â€™": "->",
        "Ã¢â€Å“Ã¢â€â‚¬": "-",
        "Ã¢â€â€Ã¢â€â‚¬": "-",
        "Ã¢â€â€š": "|",
        "Ã‚": "",
    }
    for broken, fixed in replacements.items():
        text = text.replace(broken, fixed)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def person_name_from_filename(path):
    name = Path(path).stem
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name).strip()
    name = name.replace("(OT)", "OT").replace("(NT)", "NT")
    return name


def references_from_text(text):
    book_names = sorted(BOOK_CHAPTERS, key=len, reverse=True)
    book_pattern = "|".join(re.escape(book) for book in book_names)
    pattern = re.compile(rf"\b({book_pattern})\s+(\d+)(?::(\d+)(?:\s*-\s*(\d+))?)?", re.IGNORECASE)
    refs = []
    for match in pattern.finditer(text):
        book = canonical_book_name(match.group(1))
        if not book:
            continue
        chapter = int(match.group(2))
        verse = match.group(3)
        end = match.group(4)
        if verse and end:
            ref = f"{book} {chapter}:{verse}-{end}"
        elif verse:
            ref = f"{book} {chapter}:{verse}"
        else:
            ref = f"{book} {chapter}:1"
        if ref not in refs:
            refs.append(ref)
    return refs


def infer_person_category(article):
    lower = article.lower()
    if any(word in lower for word in ("apostle", "disciple", "missionary")):
        return "New Testament Figures"
    if any(word in lower for word in ("king", "queen", "reigned", "kingdom")):
        return "Kings and Rulers"
    if any(word in lower for word in ("prophet", "prophetess")):
        return "Prophets"
    if any(word in lower for word in ("patriarch", "tribe", "covenant", "genesis")):
        return "Hebrew Bible Figures"
    return "Biblical People"


def infer_person_canon(article):
    lower = article.lower()
    if any(word in lower for word in ("gospel", "acts", "apostle", "jesus", "paul", "new testament")):
        return "New Testament"
    if any(word in lower for word in ("genesis", "exodus", "king", "prophet", "israel", "judah", "hebrew bible")):
        return "Hebrew Bible"
    return ""


def parse_people_text_file(path):
    raw = clean_imported_text(Path(path).read_text(encoding="utf-8", errors="ignore"))
    if not raw:
        return None
    name_match = re.search(r"^Name:\s*(.+)$", raw, flags=re.M)
    name = name_match.group(1).strip() if name_match else person_name_from_filename(path)
    body = re.sub(r"^Name:\s*.+\n=+\n*", "", raw, count=1, flags=re.M).strip()
    if body.lower().startswith(name.lower()):
        body = body[len(name):].strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", body, maxsplit=1)[0].strip()
    return {
        "canon": infer_person_canon(body),
        "category": infer_person_category(body),
        "roles": [],
        "summary": first_sentence or body[:280],
        "references": references_from_text(body),
        "related_people": [],
        "aliases": [person_name_from_filename(path)] if person_name_from_filename(path) != name else [],
        "article": body,
        "source": str(path),
    }


def load_people_text_profiles():
    if not PEOPLE_TEXT_DIR.exists():
        return {}
    skip_names = {"books", "biblical genealogy complete"}
    profiles = {}
    for path in PEOPLE_TEXT_DIR.glob("*.txt"):
        stem = path.stem
        if len(stem) == 1 or stem.lower() in skip_names:
            continue
        parsed = parse_people_text_file(path)
        if not parsed:
            continue
        raw = clean_imported_text(path.read_text(encoding="utf-8", errors="ignore"))
        name_match = re.search(r"^Name:\s*(.+)$", raw, flags=re.M)
        name = name_match.group(1).strip() if name_match else person_name_from_filename(path)
        profiles[name] = parsed
    return profiles


def merge_people_profiles(base, imported):
    merged = {name: dict(entry) for name, entry in base.items()}
    aliases = {alias.lower(): name for name, entry in merged.items() for alias in entry.get("aliases", [])}
    aliases.update({name.lower(): name for name in merged})
    for imported_name, imported_entry in imported.items():
        target_name = aliases.get(imported_name.lower(), imported_name)
        current = merged.setdefault(target_name, {
            "canon": "",
            "category": "",
            "roles": [],
            "summary": "",
            "references": [],
            "related_people": [],
            "aliases": [],
            "article": "",
            "source": "",
        })
        for key in ("canon", "category", "summary", "article", "source"):
            if imported_entry.get(key) and (key in ("article", "source") or not current.get(key)):
                current[key] = imported_entry[key]
        for key in ("roles", "references", "related_people", "aliases"):
            combined = list(current.get(key, []))
            for item in imported_entry.get(key, []):
                if item and item not in combined:
                    combined.append(item)
            current[key] = combined
        if imported_name != target_name and imported_name not in current["aliases"]:
            current["aliases"].append(imported_name)
    return merged


def normalize_reference_collection(items):
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        entry = dict(item)
        entry["references"] = [normalized_reference(ref) for ref in item.get("references", []) if isinstance(ref, str)]
        entry["people"] = [str(person) for person in item.get("people", []) if isinstance(person, str)]
        entry["roles"] = [str(role) for role in item.get("roles", []) if isinstance(role, str)]
        normalized.append(entry)
    return normalized


def normalize_people_reference_data(data):
    if not isinstance(data, dict):
        return {}
    return {
        "family_trees": normalize_reference_collection(data.get("family_trees", [])),
        "kings_timeline": normalize_reference_collection(data.get("kings_timeline", [])),
        "prophets_timeline": normalize_reference_collection(data.get("prophets_timeline", [])),
        "apostles": normalize_reference_collection(data.get("apostles", [])),
    }


def normalize_maps_data(data):
    if not isinstance(data, list):
        return []
    normalized = []
    for item in data:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "title": str(item.get("title", "")),
            "period": str(item.get("period", "")),
            "region": str(item.get("region", "")),
            "summary": str(item.get("summary", "")),
            "related_passages": [normalized_reference(ref) for ref in item.get("related_passages", []) if isinstance(ref, str)],
            "related_people": [str(person) for person in item.get("related_people", []) if isinstance(person, str)],
            "related_places": [str(place) for place in item.get("related_places", []) if isinstance(place, str)],
            "local_image": str(item.get("local_image", "")),
            "source_url": str(item.get("source_url", "")),
            "license": str(item.get("license", "")),
            "attribution": str(item.get("attribution", "")),
        })
    return [item for item in normalized if item.get("title")]
