"""Online Bible chapter fetching helpers."""

import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error

from bible_app.config.constants import JPS_BOOK_CODES
from bible_app.config.settings import API_RETRY_ATTEMPTS, API_TIMEOUT, BIBLE_API_URL, JPS_BASE_URL
from bible_app.core.documents import PlainTextHTMLParser
from bible_app.core.translations import clean_bible_verse_text
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)
USER_AGENT = "BibleReferenceStudyTool/0.1"


def strip_fetched_page_noise(text):
    """Remove source-page script leftovers before verse-number parsing."""
    text = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", str(text or ""))
    text = re.sub(r"\s*window\.__CF\$cv.*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"\s*\(function\(\).*?$", " ", text, flags=re.I | re.S)
    text = re.sub(r"\s*copy\(\"\"\).*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"\b\d{1,3}\s*,\s*'et\d+'\s*,.*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"\s+chapters\([^)]*$", " ", text, flags=re.I | re.S)
    return text


def fetch_url(url, timeout=API_TIMEOUT, max_retries=API_RETRY_ATTEMPTS):
    """Fetch raw bytes from a URL with logging and retry backoff.

    Args:
        url: Fully qualified URL to request.
        timeout: Request timeout in seconds.
        max_retries: Number of attempts before giving up.

    Returns:
        The response body as bytes.

    Raises:
        RuntimeError: If the request fails after all retry attempts.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Network request attempt %s/%s: %s", attempt, max_retries, url)
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
                logger.info("Network request succeeded: %s", url)
                return payload
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            logger.warning("Network request failed attempt %s/%s for %s: %s", attempt, max_retries, url, exc)
            if attempt < max_retries:
                time.sleep(2 ** (attempt - 1))
    logger.error("Network request failed after %s attempts for %s", max_retries, url)
    raise RuntimeError("Could not reach the online Bible source. Check your internet connection and try again.") from last_error


def fetch_kjv_chapter(book, chapter, max_retries=API_RETRY_ATTEMPTS):
    """Fetch one KJV chapter from bible-api.com.

    Args:
        book: Canonical Bible book name, such as ``"John"``.
        chapter: One-based chapter number.
        max_retries: Number of network attempts.

    Returns:
        List of verse strings ordered by verse number.

    Raises:
        RuntimeError: If the source cannot be reached or returns no verses.
    """
    reference = urllib.parse.quote(f"{book} {chapter}")
    url = BIBLE_API_URL.format(reference=reference)
    payload = json.loads(fetch_url(url, max_retries=max_retries).decode("utf-8"))
    verses = payload.get("verses", [])
    if not verses:
        logger.error("No KJV verses returned for %s %s", book, chapter)
        raise RuntimeError(f"No verses returned for {book} {chapter}.")
    verses.sort(key=lambda item: int(item.get("verse", 0)))
    return [item.get("text", "").strip() for item in verses]


def parse_numbered_chapter_text(text):
    """Extract verse text from a numbered public-domain chapter page.

    This is used for the JPS 1917 source, where the HTML becomes plain text
    with verse numbers embedded in the body.

    Args:
        text: Plain text containing chapter heading and numbered verses.

    Returns:
        List of verse strings in order. Returns an empty list if no numbered
        verse markers can be found.
    """
    text = strip_fetched_page_noise(text)
    text = re.sub(r"[\u0590-\u05ff\u200e\u200f\u202a-\u202e]", "", text)
    text = re.sub(r"\{[SPN]\}", " ", text)
    match = re.search(r"Chapter\s+\d+\s+(.*)", text, flags=re.S)
    body = match.group(1) if match else text
    body = re.sub(r"\s+", " ", body).strip()
    matches = list(re.finditer(r"(?:^|\s)(\d{1,3})\s+", body))
    verses = []
    for index, verse_match in enumerate(matches):
        start = verse_match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        verse = body[start:end].strip()
        verse = clean_bible_verse_text(verse)
        if verse:
            verses.append(verse)
    return verses


def fetch_jps_chapter(book, chapter, max_retries=API_RETRY_ATTEMPTS):
    """Fetch one JPS 1917 Hebrew Bible chapter.

    Args:
        book: Canonical Old Testament / Tanakh book name.
        chapter: One-based chapter number.
        max_retries: Number of network attempts.

    Returns:
        List of verse strings ordered by verse number.

    Raises:
        RuntimeError: If the book is unsupported, the source cannot be reached,
        or no verses are returned.
    """
    code = JPS_BOOK_CODES.get(book)
    if not code:
        raise RuntimeError(f"{book} is not part of the JPS 1917 Hebrew Bible.")
    url = JPS_BASE_URL.format(code=code, chapter=chapter)
    html = fetch_url(url, max_retries=max_retries).decode("utf-8", "ignore")
    parser = PlainTextHTMLParser()
    parser.feed(html)
    verses = parse_numbered_chapter_text(parser.text())
    if not verses:
        logger.error("No JPS verses returned for %s %s", book, chapter)
        raise RuntimeError(f"No verses returned for {book} {chapter}.")
    return verses


def fetch_translation_chapter(translation, book, chapter, max_retries=API_RETRY_ATTEMPTS):
    """Fetch a chapter for translations with supported online sources.

    Args:
        translation: Translation code. Currently ``"KJV"`` or ``"JPS1917"``.
        book: Canonical Bible book name.
        chapter: One-based chapter number.
        max_retries: Number of network attempts.

    Returns:
        List of verse strings.

    Raises:
        RuntimeError: If the translation cannot be fetched automatically.
    """
    if translation == "KJV":
        return fetch_kjv_chapter(book, chapter, max_retries=max_retries)
    if translation == "JPS1917":
        return fetch_jps_chapter(book, chapter, max_retries=max_retries)
    raise RuntimeError(f"{translation} chapters cannot be fetched online automatically.")
