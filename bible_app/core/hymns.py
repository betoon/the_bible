"""Hymnal PDF indexing, persistent cache, and page rendering."""

import re
from datetime import datetime
from pathlib import Path

from bible_app.config.paths import HYMNAL_INDEX_CACHE_PATH, HYMNALS_DIR
from bible_app.storage.data_manager import read_json, write_json
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


def pdf_reader_for(path):
    """Return a PDF reader for hymnal indexing, trying available libraries."""
    try:
        from pypdf import PdfReader

        return PdfReader(str(path))
    except Exception as exc:
        logger.info("pypdf could not read hymnal PDF %s; trying PyPDF2. Error: %s", path, exc)
        try:
            from PyPDF2 import PdfReader

            return PdfReader(str(path))
        except Exception as exc:
            raise RuntimeError(f"Could not read PDF. Install pypdf for PDF support. Details: {exc}") from exc


def clean_hymn_text(text):
    """Normalize common PDF text extraction artifacts in hymn text."""
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "’": "'",
        "“": '"',
        "”": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def parse_hymn_header(header):
    """Parse a hymnal page header into ``(number, section)``."""
    header = " ".join(str(header or "").split())
    if not header:
        return None, ""
    first = re.match(r"^(\d{1,4})\s+(.+)$", header)
    if first:
        return int(first.group(1)), first.group(2).strip()
    last = re.match(r"^(.+?)\s+(\d{1,4})$", header)
    if last:
        return int(last.group(2)), last.group(1).strip()
    return None, header


def looks_like_hymn_page(lines):
    """Return whether extracted PDF lines appear to describe one hymn."""
    if len(lines) < 3:
        return False
    number, section = parse_hymn_header(lines[0])
    if not number or not section:
        return False
    upper_section = section.upper()
    ignored = {"TITLE PAGE", "COMMON INDEX", "COPYING", "COPYRIGHT INFO"}
    if upper_section in ignored or "INDEX" in upper_section:
        return False
    return any(line.startswith(("Words:", "Music:", "Setting:", "copyright:")) for line in lines[2:9])


def parse_hymn_page(text, page_number):
    """Parse one extracted PDF page into hymnal index metadata.

    Returns:
        A hymn dictionary with number, section, title, page, and text, or
        ``None`` when the page is not recognized as a hymn.
    """
    lines = clean_hymn_text(text).splitlines()
    if not looks_like_hymn_page(lines):
        return None
    number, section = parse_hymn_header(lines[0])
    metadata_index = next(
        (idx for idx, line in enumerate(lines) if line.startswith(("Words:", "Music:", "Setting:", "copyright:"))),
        min(len(lines), 4),
    )
    title_candidates = [
        line for line in lines[1:metadata_index]
        if not line.startswith("(") and not re.search(r"\b[A-Z]?[a-z]{1,3}\s+\d", line)
    ]
    title = title_candidates[-1] if title_candidates else lines[2]
    return {
        "number": number,
        "section": section.title(),
        "title": title,
        "page": page_number,
        "text": "\n".join(lines),
    }


def hymnal_files():
    """Return available PDF hymnals from the configured hymnals folder."""
    if not HYMNALS_DIR.exists():
        return []
    return sorted(path for path in HYMNALS_DIR.glob("*.pdf") if path.is_file())


def build_hymnal_index(path):
    """Scan a hymnal PDF and build a list of discoverable hymns."""
    logger.info("Building hymnal index for %s", path)
    reader = pdf_reader_for(path)
    hymns = []
    for page_index, page in enumerate(reader.pages):
        try:
            item = parse_hymn_page(page.extract_text() or "", page_index + 1)
        except Exception as exc:
            logger.debug("Could not parse hymnal page %s in %s: %s", page_index + 1, path, exc)
            item = None
        if item:
            item["file"] = str(path)
            hymns.append(item)
    logger.info("Built hymnal index for %s with %s hymns", path, len(hymns))
    return hymns


def hymnal_cache_key(path):
    """Return a stable cache key for a hymnal path."""
    try:
        return str(Path(path).resolve())
    except Exception as exc:
        logger.debug("Could not resolve hymnal cache key for %s: %s", path, exc)
        return str(path)


def hymnal_cache_metadata(path):
    """Return file metadata used to invalidate stale hymnal indexes."""
    source = Path(path)
    stat = source.stat()
    return {
        "path": hymnal_cache_key(source),
        "size": stat.st_size,
        "mtime_ns": getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
    }


def cached_hymnal_entry_is_valid(path, entry):
    """Return whether a saved hymnal index still matches the source PDF."""
    if not isinstance(entry, dict):
        return False
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        return False
    try:
        current = hymnal_cache_metadata(path)
    except Exception as exc:
        logger.info("Could not validate hymnal cache metadata for %s: %s", path, exc)
        return False
    return (
        metadata.get("path") == current["path"]
        and metadata.get("size") == current["size"]
        and metadata.get("mtime_ns") == current["mtime_ns"]
        and isinstance(entry.get("hymns"), list)
    )


def read_hymnal_index_cache():
    """Load the persistent hymnal index cache."""
    data = read_json(HYMNAL_INDEX_CACHE_PATH, {})
    return data if isinstance(data, dict) else {}


def write_hymnal_index_cache(cache):
    """Save the persistent hymnal index cache."""
    write_json(HYMNAL_INDEX_CACHE_PATH, cache)


def read_cached_hymnal_index(path):
    """Return a valid cached hymnal index for ``path``, or ``None``."""
    cache = read_hymnal_index_cache()
    entry = cache.get(hymnal_cache_key(path))
    if cached_hymnal_entry_is_valid(path, entry):
        return entry.get("hymns", [])
    return None


def write_cached_hymnal_index(path, hymns):
    """Persist a hymnal index with file metadata for cache invalidation."""
    cache = read_hymnal_index_cache()
    key = hymnal_cache_key(path)
    cache[key] = {
        "metadata": hymnal_cache_metadata(path),
        "created": datetime.now().isoformat(timespec="seconds"),
        "hymns": hymns,
    }
    write_hymnal_index_cache(cache)
    logger.info("Cached hymnal index for %s with %s hymns", path, len(hymns))


def load_hymnal_index(path):
    """Load a hymnal index from cache or build and cache it.

    Returns:
        ``(hymns, from_cache)`` where ``from_cache`` is ``True`` when no PDF
        scan was needed.
    """
    cached = read_cached_hymnal_index(path)
    if cached is not None:
        logger.info("Loaded hymnal index from cache for %s", path)
        return cached, True
    hymns = build_hymnal_index(path)
    write_cached_hymnal_index(path, hymns)
    return hymns, False


def render_pdf_page_image(path, page_number, zoom=1.35):
    """Render a hymnal PDF page to a PIL image for the sheet music viewer."""
    page_index = max(0, int(page_number) - 1)
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(path))
        try:
            page = pdf[page_index]
            try:
                bitmap = page.render(scale=float(zoom))
                return bitmap.to_pil()
            finally:
                page.close()
        finally:
            pdf.close()
    except Exception as exc:
        logger.info("pypdfium2 could not render %s page %s; trying PyMuPDF. Error: %s", path, page_number, exc)
        try:
            import fitz

            doc = fitz.open(str(path))
            try:
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=fitz.Matrix(float(zoom), float(zoom)), alpha=False)
                from PIL import Image

                return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            finally:
                doc.close()
        except Exception as exc:
            raise RuntimeError(f"Could not render PDF page. Install pypdfium2 or PyMuPDF for sheet music viewing. Details: {exc}") from exc
