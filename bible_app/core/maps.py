"""Map metadata, discovery, merging, and image resolution."""

import re
from pathlib import Path

from bible_app.config.paths import APP_DIR, MAPS_ASSET_DIR, MAPS_DIR, RESOURCE_DIR
from bible_app.core.references import normalized_reference


def map_title_from_path(path):
    title = Path(path).stem.replace("_", " ")
    title = re.sub(r"^\d+\s+", "", title)
    return re.sub(r"\s+", " ", title).strip()


def infer_map_metadata(title):
    lower = title.lower()
    people = []
    passages = []
    places = []
    period = ""
    region = ""
    if "abraham" in lower or "patriarch" in lower:
        people.extend(["Abraham", "Sarah", "Isaac", "Jacob"])
        passages.extend(["Genesis 12:1", "Genesis 15:18"])
        places.extend(["Canaan", "Ancient Near East"])
        period = "Patriarchal narratives"
        region = "Canaan / Ancient Near East"
    if "exodus" in lower or "wander" in lower:
        people.extend(["Moses", "Aaron", "Miriam", "Joshua"])
        passages.extend(["Exodus 12:31", "Exodus 14:21", "Numbers 14:25"])
        places.extend(["Egypt", "Sinai", "Transjordan"])
        period = "Exodus / wilderness"
        region = "Egypt, Sinai, Transjordan"
    if "paul" in lower or "acts" in lower:
        people.extend(["Paul", "Barnabas", "Silas", "Timothy", "Luke"])
        passages.extend(["Acts 9:1", "Acts 13:4", "Acts 16:9", "Romans 1:1"])
        places.extend(["Eastern Mediterranean", "Rome"])
        period = "Early church"
        region = "Eastern Mediterranean"
    if "jesus" in lower or "herod" in lower:
        people.extend(["Jesus", "Mary the Mother of Jesus", "John the Baptist", "Herod the Great", "Herod Antipas"])
        passages.extend(["Luke 2:7", "John 2:1", "John 19:17"])
        places.extend(["Judea", "Galilee", "Jerusalem"])
        period = "Gospel period"
        region = "Judea / Galilee"
    if "david" in lower or "solomon" in lower or "saul" in lower or "divided kingdom" in lower:
        people.extend(["Saul", "David", "Solomon", "Rehoboam", "Jeroboam I"])
        passages.extend(["1 Samuel 10:1", "2 Samuel 5:3", "1 Kings 1:39", "1 Kings 12:20"])
        places.extend(["Israel", "Judah", "Jerusalem"])
        period = "United and divided monarchy"
        region = "Israel and Judah"
    if "canaan" in lower or "promised land" in lower or "tribal" in lower or "joshua" in lower:
        people.extend(["Abraham", "Isaac", "Jacob", "Joshua"])
        passages.extend(["Genesis 12:1", "Joshua 1:1", "Joshua 13:1"])
        places.append("Canaan")
        region = "Canaan"
    if "near east" in lower or "persian" in lower or "assyrian" in lower or "greek" in lower or "roman" in lower:
        places.append("Ancient Near East" if "near east" in lower else "Mediterranean")
        region = region or "Ancient Near East / Mediterranean"
    return {
        "period": period,
        "region": region,
        "summary": f"Discovered map asset: {title}.",
        "related_passages": list(dict.fromkeys(normalized_reference(ref) for ref in passages)),
        "related_people": list(dict.fromkeys(people)),
        "related_places": list(dict.fromkeys(places)),
    }


def discover_map_assets():
    maps = []
    seen_paths = set()
    for map_dir in (MAPS_ASSET_DIR, MAPS_DIR):
        if not map_dir.exists():
            continue
        for path in sorted(map_dir.iterdir()):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            path_key = str(path.resolve()).lower()
            if path_key in seen_paths:
                continue
            seen_paths.add(path_key)
            title = map_title_from_path(path)
            metadata = infer_map_metadata(title)
            maps.append({
                "title": title,
                "period": metadata["period"],
                "region": metadata["region"],
                "summary": metadata["summary"],
                "related_passages": metadata["related_passages"],
                "related_people": metadata["related_people"],
                "related_places": metadata["related_places"],
                "local_image": str(path),
                "source_url": "",
                "license": "Local map asset",
                "attribution": "",
            })
    return maps


def map_match_key(title):
    words = re.sub(r"[^a-z0-9]+", " ", str(title).lower()).split()
    skip = {"and", "of", "the", "during", "time", "under"}
    return " ".join(word for word in words if word not in skip)


def map_titles_are_related(left, right):
    left_key = map_match_key(left)
    right_key = map_match_key(right)
    if not left_key or not right_key:
        return False
    left_words = set(left_key.split())
    right_words = set(right_key.split())
    return left_key in right_key or right_key in left_key or len(left_words & right_words) >= 2


def preferred_map_asset_title(title):
    lower = str(title).lower()
    if "exodus" in lower or "wilderness" in lower:
        return "Israels Exodus and Wanderings"
    if "monarchy" in lower or "kingdom" in lower:
        return "The Divided Kingdom"
    if "jerusalem" in lower:
        return "Israel During the Time of Jesus"
    if "paul" in lower or "journey" in lower:
        return "Pauls First Missionary Journey"
    return ""


def merge_discovered_maps(base_maps, discovered_maps):
    merged = list(base_maps)
    seen_images = {str(item.get("local_image", "")).lower() for item in merged if item.get("local_image")}
    seen_titles = {str(item.get("title", "")).lower() for item in merged}
    discovered_by_title = {str(item.get("title", "")).lower(): item for item in discovered_maps}
    for item in discovered_maps:
        image_key = str(item.get("local_image", "")).lower()
        title_key = str(item.get("title", "")).lower()
        if image_key in seen_images:
            continue
        matched = None
        for existing in merged:
            if map_titles_are_related(existing.get("title", ""), item.get("title", "")):
                matched = existing
                break
        if matched and not matched.get("local_image"):
            matched["local_image"] = item.get("local_image", "")
            for key in ("period", "region", "summary", "license", "attribution", "source_url"):
                if item.get(key) and not matched.get(key):
                    matched[key] = item[key]
            for key in ("related_passages", "related_people", "related_places"):
                combined = list(matched.get(key, []))
                for value in item.get(key, []):
                    if value and value not in combined:
                        combined.append(value)
                matched[key] = combined
            seen_images.add(image_key)
            continue
        if title_key in seen_titles:
            continue
        merged.append(item)
        seen_images.add(image_key)
        seen_titles.add(title_key)
    for existing in merged:
        if existing.get("local_image"):
            continue
        preferred_title = preferred_map_asset_title(existing.get("title", ""))
        preferred = discovered_by_title.get(preferred_title.lower())
        if preferred and preferred.get("local_image"):
            existing["local_image"] = preferred["local_image"]
    return merged


def resolve_local_map_image(image_path):
    if not image_path:
        return ""
    path = Path(image_path)
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([APP_DIR / path, RESOURCE_DIR / path, MAPS_ASSET_DIR / path, MAPS_DIR / path])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(path)
