"""Bible reference parsing and normalization."""

import re

from bible_app.config.constants import BOOK_CHAPTERS, BOOK_ORDER


BOOK_ALIASES = {
    "psalms": "Psalm",
    "ps": "Psalm",
    "psa": "Psalm",
    "song": "Song of Solomon",
    "song of songs": "Song of Solomon",
    "jn": "John",
    "jhn": "John",
    "rev": "Revelation",
}
for book_name in BOOK_ORDER:
    BOOK_ALIASES[book_name.lower()] = book_name
    BOOK_ALIASES[book_name.replace(" ", "").lower()] = book_name
    BOOK_ALIASES[book_name.replace("1 ", "1").replace("2 ", "2").replace("3 ", "3").lower()] = book_name


def canonical_book_name(book):
    """Return the canonical book name for common aliases and spacing styles."""
    compact = re.sub(r"\s+", " ", str(book).strip()).lower()
    squashed = compact.replace(" ", "")
    return BOOK_ALIASES.get(compact) or BOOK_ALIASES.get(squashed)


def reference_parts(ref):
    """Parse a single-verse reference.

    Args:
        ref: Reference such as ``"John 3:16"`` or ``"Psalm 23"``.

    Returns:
        ``(book, chapter, verse)`` or ``None`` when parsing fails. A missing
        verse defaults to verse 1.
    """
    match = re.match(r"^(.+?)\s+(\d+)(?::(\d+))?$", str(ref).strip())
    if not match:
        return None
    book = canonical_book_name(match.group(1))
    if not book:
        return None
    return book, int(match.group(2)), int(match.group(3) or 1)


def reference_range_parts(ref):
    """Parse a same-chapter verse range like ``"Romans 8:1-4"``.

    Returns:
        ``(book, chapter, start_verse, end_verse)`` or ``None``.
    """
    match = re.match(r"^(.+?)\s+(\d+):(\d+)\s*-\s*(\d+)$", str(ref).strip())
    if not match:
        return None
    book = canonical_book_name(match.group(1))
    if not book:
        return None
    chapter = int(match.group(2))
    start = int(match.group(3))
    end = int(match.group(4))
    if start <= 0 or end < start:
        return None
    return book, chapter, start, end


def is_range_reference(ref):
    """Return whether ``ref`` is a supported same-chapter verse range."""
    return reference_range_parts(ref) is not None


def normalized_reference(ref):
    """Return a canonical display form for a reference when possible."""
    range_parts = reference_range_parts(ref)
    if range_parts:
        book, chapter, start, end = range_parts
        return f"{book} {chapter}:{start}-{end}"
    parts = reference_parts(ref)
    if parts:
        book, chapter, verse = parts
        return f"{book} {chapter}:{verse}"
    return str(ref).strip()
