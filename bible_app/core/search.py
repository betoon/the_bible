"""Search helpers for Bible text and word studies."""

import re

from bible_app.config.constants import BOOK_ORDER
from bible_app.core.references import reference_parts


def word_occurrences(translation_data, query):
    query = str(query or "").strip()
    if not query:
        return []
    matches = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for book, chapters in translation_data.items():
        for chapter, verses in chapters.items():
            for verse_num, verse_text in enumerate(verses, 1):
                verse_matches = pattern.findall(str(verse_text))
                if verse_matches:
                    matches.append({
                        "reference": f"{book} {chapter}:{verse_num}",
                        "text": verse_text,
                        "count": len(verse_matches),
                    })
    return matches


def reference_sort_key(ref):
    parts = reference_parts(ref)
    if not parts:
        return (999, 999, 999)
    book, chapter, verse = parts
    try:
        book_index = BOOK_ORDER.index(book)
    except ValueError:
        book_index = 999
    return (book_index, chapter, verse)


def search_bible(translation_data, query, exact_phrase=False, whole_word=False, books=None, sort_mode="Book order", context=False):
    query = str(query or "").strip()
    if not query:
        return []
    flags = re.IGNORECASE
    if exact_phrase:
        pattern_text = re.escape(query)
    else:
        pattern_text = r"\s+".join(re.escape(part) for part in query.split())
    if whole_word:
        pattern_text = rf"\b{pattern_text}\b"
    pattern = re.compile(pattern_text, flags)
    matches = []
    for book, chapters in translation_data.items():
        if books and book not in books:
            continue
        for chapter, verses in chapters.items():
            for verse_num, verse_text in enumerate(verses, 1):
                text = str(verse_text)
                found = pattern.findall(text)
                if not found:
                    continue
                preview = text
                if context:
                    first = pattern.search(text)
                    if first:
                        start = max(0, first.start() - 55)
                        end = min(len(text), first.end() + 75)
                        preview = ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")
                matches.append({
                    "reference": f"{book} {chapter}:{verse_num}",
                    "text": text,
                    "preview": preview,
                    "count": len(found),
                })
    if sort_mode == "Relevance":
        matches.sort(key=lambda item: (-item["count"], reference_sort_key(item["reference"])))
    else:
        matches.sort(key=lambda item: reference_sort_key(item["reference"]))
    return matches
