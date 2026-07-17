"""Stable Bible constants used by pure modules.

The full legacy app still owns the complete starter Bible/sample data during
phase 1. Constants moved here are the small, stable pieces needed by extracted
helpers and tests.
"""

BOOK_CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
    "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalm": 150, "Proverbs": 31,
    "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52,
    "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3,
    "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3,
    "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4, "Matthew": 28,
    "Mark": 16, "Luke": 24, "John": 21, "Acts": 28, "Romans": 16, "1 Corinthians": 16,
    "2 Corinthians": 13, "Galatians": 6, "Ephesians": 6, "Philippians": 4, "Colossians": 4,
    "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4,
    "Titus": 3, "Philemon": 1, "Hebrews": 13, "James": 5, "1 Peter": 5,
    "2 Peter": 3, "1 John": 5, "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22,
}

BOOK_ORDER = list(BOOK_CHAPTERS.keys())
OLD_TESTAMENT_BOOKS = BOOK_ORDER[:39]
NEW_TESTAMENT_BOOKS = BOOK_ORDER[39:]
TANAKH_BOOKS = OLD_TESTAMENT_BOOKS
TORAH_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
PROPHETS_BOOKS = [
    "Joshua", "Judges", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah",
    "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi",
]
WRITINGS_BOOKS = [
    "Psalm", "Proverbs", "Job", "Song of Solomon", "Ruth", "Lamentations",
    "Ecclesiastes", "Esther", "Daniel", "Ezra", "Nehemiah",
    "1 Chronicles", "2 Chronicles",
]
JPS_BOOK_CODES = {
    "Genesis": "et01", "Exodus": "et02", "Leviticus": "et03", "Numbers": "et04", "Deuteronomy": "et05",
    "Joshua": "et06", "Judges": "et07", "1 Samuel": "et08a", "2 Samuel": "et08b",
    "1 Kings": "et09a", "2 Kings": "et09b", "Isaiah": "et10", "Jeremiah": "et11", "Ezekiel": "et12",
    "Hosea": "et13", "Joel": "et14", "Amos": "et15", "Obadiah": "et16", "Jonah": "et17",
    "Micah": "et18", "Nahum": "et19", "Habakkuk": "et20", "Zephaniah": "et21", "Haggai": "et22",
    "Zechariah": "et23", "Malachi": "et24", "1 Chronicles": "et25a", "2 Chronicles": "et25b",
    "Psalm": "et26", "Job": "et27", "Proverbs": "et28", "Ruth": "et29", "Song of Solomon": "et30",
    "Ecclesiastes": "et31", "Lamentations": "et32", "Esther": "et33", "Daniel": "et34",
    "Ezra": "et35a", "Nehemiah": "et35b",
}
