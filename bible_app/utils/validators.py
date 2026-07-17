"""Input validation helpers."""

from bible_app.config.constants import BOOK_CHAPTERS
from bible_app.core.references import normalized_reference, reference_parts, reference_range_parts


def validate_bible_reference(reference):
    """Return normalized reference parts or raise ValueError.

    Returns:
        (book, chapter, verse) for single-verse references.
        (book, chapter, start_verse, end_verse) for verse ranges.
    """
    raw = str(reference or "").strip()
    if not raw:
        raise ValueError("Enter a Bible reference.")

    range_parts = reference_range_parts(raw)
    if range_parts:
        book, chapter, start, end = range_parts
        validate_chapter(book, chapter)
        if start < 1 or end < start:
            raise ValueError("Verse range is not valid.")
        return book, chapter, start, end

    parts = reference_parts(raw)
    if not parts:
        raise ValueError("Use a reference like John 3:16 or Psalm 23:1-6.")

    book, chapter, verse = parts
    validate_chapter(book, chapter)
    if verse < 1:
        raise ValueError("Verse number must be 1 or higher.")
    return book, chapter, verse


def validate_chapter(book, chapter):
    """Raise ``ValueError`` when a chapter is outside the canonical range."""
    if book not in BOOK_CHAPTERS:
        raise ValueError(f"{book} is not a recognized Bible book.")
    if chapter < 1 or chapter > BOOK_CHAPTERS[book]:
        raise ValueError(f"{book} has chapters 1-{BOOK_CHAPTERS[book]}.")


def is_reference(value):
    """Return whether a value can be parsed as a supported Bible reference."""
    try:
        validate_bible_reference(value)
        return True
    except ValueError:
        return False


def clean_reference(value):
    """Return a normalized reference string, or an empty string if invalid."""
    return normalized_reference(value) if is_reference(value) else ""
