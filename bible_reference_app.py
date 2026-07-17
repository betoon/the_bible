import json
import os
import re
import shutil
import sys
from datetime import datetime
import threading
import tkinter as tk
import urllib.parse
import urllib.request
from pathlib import Path
from html.parser import HTMLParser
from tkinter import colorchooser, filedialog, font as tkfont, messagebox, simpledialog, ttk

from bible_app.config.settings import (
    APP_SETTINGS,
    AUTO_BACKUP_ON_STARTUP,
    CONNECTION_CHECK_TIMEOUT,
    DEFAULT_TRANSLATION,
    MAX_BACKUPS,
    PASSAGE_CACHE_SIZE,
)
from bible_app.core.cache import BibleLookupCache
from bible_app.ui.styles import configure_app_styles
from bible_app.ui.window_config import configure_window_size
from bible_app.utils.background import BackgroundTaskRunner
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))


def default_user_data_dir():
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "BibleReferenceStudyTool"


USER_DATA_DIR = Path(os.environ.get("BIBLE_APP_USER_DATA_DIR", default_user_data_dir()))
DATA_DIR = USER_DATA_DIR / "data"
APP_DATA_DIR = RESOURCE_DIR / "data"
BUNDLED_ENGLISH_DIR = APP_DATA_DIR / "EN-English"
BIBLE_DATA_PATH = DATA_DIR / "kjv_bible.json"
NOTES_PATH = USER_DATA_DIR / "bible_personal_notes.json"
JOURNAL_PATH = USER_DATA_DIR / "bible_private_journal.json"
BOOKMARKS_PATH = USER_DATA_DIR / "bible_bookmarks.json"
HIGHLIGHTS_PATH = USER_DATA_DIR / "bible_highlights.json"
CONCEPTS_PATH = USER_DATA_DIR / "bible_concepts.json"
STUDY_SESSIONS_PATH = USER_DATA_DIR / "bible_study_sessions.json"
READING_PLANS_PATH = USER_DATA_DIR / "bible_reading_plans.json"
WORKSHEETS_PATH = USER_DATA_DIR / "bible_study_worksheets.json"
HYMN_LINKS_PATH = USER_DATA_DIR / "bible_hymn_links.json"
HYMN_FAVORITES_PATH = USER_DATA_DIR / "bible_hymn_favorites.json"
RECENT_HYMNS_PATH = USER_DATA_DIR / "bible_recent_hymns.json"
RECENT_REFERENCES_PATH = USER_DATA_DIR / "bible_recent_references.json"
USER_CROSS_REFERENCES_PATH = USER_DATA_DIR / "bible_user_cross_references.json"
SETTINGS_PATH = USER_DATA_DIR / "bible_settings.json"
BACKUP_DIR = USER_DATA_DIR / "backups"
EXPORT_DIR = USER_DATA_DIR / "exports"
COMMENTARY_DIR = USER_DATA_DIR / "commentary"
DOCUMENT_LIBRARY_DIR = USER_DATA_DIR / "documents"
DOCUMENT_LIBRARY_PATH = DOCUMENT_LIBRARY_DIR / "library.json"
DOCUMENT_IMAGE_DIR = DOCUMENT_LIBRARY_DIR / "images"
HYMNAL_INDEX_CACHE_PATH = USER_DATA_DIR / "hymnal_index_cache.json"
STUDY_DATA_DIR = RESOURCE_DIR / "study_data"
STUDY_DATA_PATH = STUDY_DATA_DIR / "study_notes.json"
THEMES_DATA_PATH = STUDY_DATA_DIR / "themes.json"
PEOPLE_DATA_PATH = STUDY_DATA_DIR / "people.json"
PEOPLE_REFERENCE_PATH = STUDY_DATA_DIR / "people_reference.json"
MAPS_DATA_PATH = STUDY_DATA_DIR / "maps.json"
MAPS_DIR = RESOURCE_DIR / "maps"
PEOPLE_TEXT_DIR = APP_DATA_DIR / "people"
MAPS_ASSET_DIR = APP_DATA_DIR / "maps"
NIV_PDF_PATH = APP_DATA_DIR / "NIV-Bible.pdf"
HYMNALS_DIR = APP_DATA_DIR / "hymnals"
BIBLE_API_URL = "https://bible-api.com/{reference}?translation=kjv"
JPS_BASE_URL = "https://www.mechon-mamre.org/e/et/{code}{chapter:02d}.htm"
APP_BG = "#F3F3F3"
APP_PANEL = "#FFFFFF"
TRANSLATION_LABELS = {
    "KJV": "King James Version",
    "JPS1917": "JPS 1917 Hebrew Bible / Tanakh",
    "NIV": "New International Version",
    "ESV": "English Standard Version",
}
BUNDLED_TRANSLATION_LABELS = {}


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


BIBLE = {
    "KJV": {
        "Genesis": {
            1: [
                "In the beginning God created the heaven and the earth.",
                "And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
                "And God said, Let there be light: and there was light.",
                "And God saw the light, that it was good: and God divided the light from the darkness.",
                "And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day.",
            ]
        },
        "Psalm": {
            23: [
                "The LORD is my shepherd; I shall not want.",
                "He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
                "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
                "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.",
                "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over.",
                "Surely goodness and mercy shall follow me all the days of my life: and I will dwell in the house of the LORD for ever.",
            ]
        },
        "Isaiah": {
            53: [
                "Who hath believed our report? and to whom is the arm of the LORD revealed?",
                "For he shall grow up before him as a tender plant, and as a root out of a dry ground.",
                "He is despised and rejected of men; a man of sorrows, and acquainted with grief.",
                "Surely he hath borne our griefs, and carried our sorrows.",
                "But he was wounded for our transgressions, he was bruised for our iniquities.",
            ]
        },
        "John": {
            1: [
                "In the beginning was the Word, and the Word was with God, and the Word was God.",
                "The same was in the beginning with God.",
                "All things were made by him; and without him was not any thing made that was made.",
                "In him was life; and the life was the light of men.",
                "And the light shineth in darkness; and the darkness comprehended it not.",
            ],
            3: [
                "There was a man of the Pharisees, named Nicodemus, a ruler of the Jews.",
                "The same came to Jesus by night, and said unto him, Rabbi, we know that thou art a teacher come from God.",
                "Jesus answered and said unto him, Except a man be born again, he cannot see the kingdom of God.",
                "For God so loved the world, that he gave his only begotten Son.",
                "For God sent not his Son into the world to condemn the world; but that the world through him might be saved.",
            ],
        },
        "Romans": {
            8: [
                "There is therefore now no condemnation to them which are in Christ Jesus.",
                "For the law of the Spirit of life in Christ Jesus hath made me free from the law of sin and death.",
                "For to be carnally minded is death; but to be spiritually minded is life and peace.",
                "The Spirit itself beareth witness with our spirit, that we are the children of God.",
                "And we know that all things work together for good to them that love God.",
            ]
        },
        "1 Corinthians": {
            13: [
                "Though I speak with the tongues of men and of angels, and have not charity, I am become as sounding brass.",
                "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up.",
                "Charity never faileth.",
                "And now abideth faith, hope, charity, these three; but the greatest of these is charity.",
            ]
        },
    }
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

GOSPEL_BOOKS = {"Matthew", "Mark", "Luke", "John"}
OLD_TESTAMENT_BOOKS = set(BOOK_ORDER[:39])
NEW_TESTAMENT_BOOKS = set(BOOK_ORDER[39:])
SEARCH_RANGES = {
    "Whole Bible": None,
    "Old Testament": OLD_TESTAMENT_BOOKS,
    "New Testament": NEW_TESTAMENT_BOOKS,
    "Gospels": GOSPEL_BOOKS,
    "Current Book": "current_book",
}
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

THEMES = {
    "Creation": ["Genesis 1:1", "Genesis 1:3", "John 1:3"],
    "Light": ["Genesis 1:3", "John 1:4", "John 1:5"],
    "Shepherd": ["Psalm 23:1", "Psalm 23:2", "Psalm 23:4"],
    "Salvation": ["Isaiah 53:5", "John 3:3", "John 3:5", "Romans 8:1"],
    "Love": ["John 3:4", "Romans 8:5", "1 Corinthians 13:2", "1 Corinthians 13:4"],
}

DEFAULT_CONCEPTS = [
    {
        "name": "Apocrypha / Deuterocanonical Books",
        "category": "Second Temple / Canon Study",
        "summary": "Study the books received differently across Jewish, Catholic, Orthodox, and Protestant traditions. Useful for understanding historical background, wisdom traditions, and the world between the Testaments.",
        "references": ["Daniel 3:24", "Daniel 12:2", "Hebrews 11:35"],
        "related_readings": ["Tobit", "Judith", "Wisdom of Solomon", "Sirach", "Baruch", "1 Maccabees", "2 Maccabees", "Additions to Daniel", "Additions to Esther"],
        "notes": "If you import public-domain Apocrypha text later, this concept can link directly into those passages.",
        "sources": ["Public-domain KJV Apocrypha editions", "Sefaria for related Jewish texts", "public-domain encyclopedia articles for historical background"],
    },
    {
        "name": "Apocryphal Letters",
        "category": "Early Christian / Historical Study",
        "summary": "Study letters and writings associated with early Christian communities but not included in the New Testament canon. Treat these as historical witnesses, not as biblical text inside the app unless separately imported and labeled.",
        "references": ["Colossians 4:16", "2 Thessalonians 2:2", "Jude 1:14"],
        "related_readings": ["Epistle of Barnabas", "1 Clement", "2 Clement", "Letters of Ignatius", "Letter of Polycarp", "Shepherd of Hermas"],
        "notes": "A useful study question: what did early Christians quote, preserve, dispute, or distinguish from apostolic Scripture?",
        "sources": ["Early Christian Writings", "Christian Classics Ethereal Library", "public-domain translations where available"],
    },
    {
        "name": "Precepts / Commands",
        "category": "Ethics / Obedience",
        "summary": "Trace commands, statutes, instruction, and obedience across Torah, wisdom literature, Jesus' teaching, and the letters.",
        "references": ["Deuteronomy 6:5", "Psalm 119:4", "Matthew 22:37", "John 14:15", "1 John 5:3"],
        "related_readings": ["Psalm 119", "Sermon on the Mount", "James"],
        "notes": "",
        "sources": ["Nave's Topical Bible", "Torrey's Topical Textbook"],
    },
    {
        "name": "Corinthians: Church, Gifts, and Love",
        "category": "Pauline Letters",
        "summary": "Study the Corinthian letters around unity, spiritual gifts, resurrection, discipline, holiness, and love.",
        "references": ["1 Corinthians 1:10", "1 Corinthians 12:4", "1 Corinthians 13:4", "1 Corinthians 15:3", "2 Corinthians 5:17"],
        "related_readings": ["Acts 18", "1 Corinthians", "2 Corinthians"],
        "notes": "",
        "sources": ["Treasury of Scripture Knowledge", "public-domain Bible dictionaries"],
    },
    {
        "name": "Covenant",
        "category": "Biblical Theology",
        "summary": "Trace covenant promises and obligations from Noah, Abraham, Sinai, David, the prophets, and the New Covenant.",
        "references": ["Genesis 9:9", "Genesis 12:2", "Exodus 19:5", "2 Samuel 7:12", "Jeremiah 31:31", "Luke 22:20"],
        "related_readings": ["Genesis 15", "Exodus 24", "Hebrews 8"],
        "notes": "",
        "sources": ["Nave's Topical Bible", "Torrey's Topical Textbook"],
    },
    {
        "name": "Resurrection",
        "category": "Doctrine / Hope",
        "summary": "Study resurrection hope in the prophets, Gospels, Acts, Paul, and Revelation.",
        "references": ["Daniel 12:2", "John 11:25", "Acts 2:24", "1 Corinthians 15:20", "Revelation 20:6"],
        "related_readings": ["1 Corinthians 15", "John 20"],
        "notes": "",
        "sources": ["Treasury of Scripture Knowledge", "International Standard Bible Encyclopedia 1915"],
    },
]

STUDY = {
    "Genesis 1:1": {
        "teaching": "A foundational verse for creation, origin, and divine agency.",
        "cross": ["John 1:1", "John 1:3"],
        "language": [("created", "bara", "Hebrew verb often associated with God's creative action.")],
        "map": "Ancient Near East context: creation narrative, no single journey location.",
    },
    "Psalm 23:1": {
        "teaching": "The shepherd image presents God as provider, guide, protector, and host.",
        "cross": ["John 10:11", "Psalm 23:4"],
        "language": [("LORD", "YHWH", "Covenant name of God in the Hebrew Bible.")],
        "map": "Pastoral imagery from ancient Israel and Judah.",
    },
    "John 1:1": {
        "teaching": "John opens by connecting Jesus, the Word, with creation and divine identity.",
        "cross": ["Genesis 1:1", "Genesis 1:3", "John 1:3"],
        "language": [("Word", "Logos", "Greek term carrying meaning of word, reason, message, or ordering principle.")],
        "map": "John's Gospel moves through Judea, Galilee, and Jerusalem.",
    },
    "John 3:4": {
        "teaching": "A compact summary of divine love and salvation. In the full Bible this corresponds to John 3:16.",
        "cross": ["Romans 8:1", "1 Corinthians 13:4"],
        "language": [("loved", "agapao", "Greek verb associated with self-giving love.")],
        "map": "Conversation with Nicodemus, traditionally associated with Jerusalem.",
    },
    "Romans 8:1": {
        "teaching": "A key verse for assurance, grace, and freedom from condemnation in Christ.",
        "cross": ["John 3:5", "Romans 8:2"],
        "language": [("condemnation", "katakrima", "Judicial term for sentence or penalty.")],
        "map": "Paul's letter to believers in Rome.",
    },
}

DEFAULT_THEMES = json.loads(json.dumps(THEMES))
DEFAULT_STUDY = json.loads(json.dumps(STUDY))
DEFAULT_PEOPLE = {
    "Adam": {
        "canon": "Hebrew Bible",
        "category": "Primeval figures",
        "roles": ["first human"],
        "summary": "The first man in Genesis, placed in Eden and named as an ancestor of humanity.",
        "references": ["Genesis 1:26", "Genesis 2:7", "Genesis 3:17"],
        "related_people": ["Eve", "Seth", "Cain", "Abel"],
    },
    "Abraham": {
        "canon": "Hebrew Bible",
        "category": "Patriarchs",
        "roles": ["patriarch", "ancestor"],
        "summary": "Called by God to leave his country and associated with the covenant promises of land, descendants, and blessing.",
        "references": ["Genesis 12:1", "Genesis 15:6", "Genesis 17:5"],
        "related_people": ["Sarah", "Isaac", "Ishmael", "Lot"],
    },
    "Moses": {
        "canon": "Hebrew Bible",
        "category": "Prophets",
        "roles": ["prophet", "leader", "lawgiver"],
        "summary": "Leader of Israel in the Exodus tradition and central figure in the giving of the Torah.",
        "references": ["Exodus 3:1", "Exodus 12:31", "Deuteronomy 34:10"],
        "related_people": ["Aaron", "Miriam", "Pharaoh", "Joshua"],
    },
    "David": {
        "canon": "Hebrew Bible",
        "category": "Kings",
        "roles": ["king", "psalmist"],
        "summary": "King of Israel associated with Jerusalem, the Davidic dynasty, and many psalms.",
        "references": ["1 Samuel 16:13", "2 Samuel 5:3", "Psalm 23:1"],
        "related_people": ["Saul", "Jonathan", "Solomon", "Bathsheba"],
    },
    "Mary, mother of Jesus": {
        "canon": "New Testament",
        "category": "Jesus and his relatives",
        "roles": ["mother of Jesus"],
        "summary": "Mother of Jesus, present in the infancy narratives and later scenes in the Gospels and Acts.",
        "references": ["Luke 1:30", "Luke 2:7", "John 19:26"],
        "related_people": ["Jesus", "Joseph", "Elizabeth"],
    },
    "Jesus": {
        "canon": "New Testament",
        "category": "Jesus and his relatives",
        "roles": ["Messiah", "teacher", "Son of God"],
        "summary": "Central figure of the New Testament, presented in the Gospels as teacher, healer, crucified and risen Lord.",
        "references": ["Matthew 1:1", "John 1:1", "John 3:16"],
        "related_people": ["Mary, mother of Jesus", "John the Baptist", "Peter", "Paul"],
    },
    "Peter": {
        "canon": "New Testament",
        "category": "Apostles",
        "roles": ["apostle", "disciple"],
        "summary": "One of Jesus's leading apostles, prominent in the Gospels and early chapters of Acts.",
        "references": ["Matthew 4:18", "Matthew 16:16", "Acts 2:14"],
        "related_people": ["Andrew", "Jesus", "John"],
    },
    "Paul": {
        "canon": "New Testament",
        "category": "Apostles",
        "roles": ["apostle", "missionary", "letter writer"],
        "summary": "Apostle to the Gentiles and author or associated sender of many New Testament letters.",
        "references": ["Acts 9:1", "Romans 1:1", "Philippians 1:1"],
        "related_people": ["Barnabas", "Silas", "Timothy", "Luke"],
    },
}
DEFAULT_PEOPLE_REFERENCE = {
    "family_trees": [
        {
            "name": "Primeval Family",
            "people": ["Adam", "Eve", "Cain", "Abel", "Seth", "Noah"],
            "notes": "Early Genesis family line from the first humans toward Noah.",
            "references": ["Genesis 4:1", "Genesis 4:25", "Genesis 5:29"],
        },
        {
            "name": "Patriarchs",
            "people": ["Abraham", "Sarah", "Isaac", "Rebekah", "Jacob", "Esau", "Joseph"],
            "notes": "The ancestral family line central to Genesis.",
            "references": ["Genesis 12:1", "Genesis 21:3", "Genesis 25:26", "Genesis 37:3"],
        },
        {
            "name": "Davidic House",
            "people": ["David", "Bathsheba", "Solomon", "Rehoboam"],
            "notes": "Royal line associated with Jerusalem and the kingdom of Judah.",
            "references": ["2 Samuel 5:3", "2 Samuel 12:24", "1 Kings 11:43"],
        },
        {
            "name": "Jesus and Relatives",
            "people": ["Mary, mother of Jesus", "Joseph", "Jesus", "Elizabeth", "John the Baptist"],
            "notes": "New Testament family and kinship circle around Jesus.",
            "references": ["Luke 1:30", "Luke 1:57", "Luke 2:7"],
        },
    ],
    "kings_timeline": [
        {"name": "Saul", "kingdom": "Israel", "period": "United monarchy", "references": ["1 Samuel 10:1"]},
        {"name": "David", "kingdom": "Israel", "period": "United monarchy", "references": ["2 Samuel 5:3"]},
        {"name": "Solomon", "kingdom": "Israel", "period": "United monarchy", "references": ["1 Kings 1:39"]},
        {"name": "Rehoboam", "kingdom": "Judah", "period": "Divided monarchy", "references": ["1 Kings 12:17"]},
        {"name": "Jeroboam", "kingdom": "Israel", "period": "Divided monarchy", "references": ["1 Kings 12:20"]},
        {"name": "Hezekiah", "kingdom": "Judah", "period": "Assyrian crisis", "references": ["2 Kings 18:1"]},
        {"name": "Josiah", "kingdom": "Judah", "period": "Late monarchy", "references": ["2 Kings 22:1"]},
    ],
    "prophets_timeline": [
        {"name": "Moses", "period": "Exodus / wilderness", "references": ["Exodus 3:1", "Deuteronomy 34:10"]},
        {"name": "Samuel", "period": "Transition to monarchy", "references": ["1 Samuel 3:20"]},
        {"name": "Elijah", "period": "Northern kingdom", "references": ["1 Kings 17:1"]},
        {"name": "Elisha", "period": "Northern kingdom", "references": ["2 Kings 2:15"]},
        {"name": "Isaiah", "period": "Judah / Assyrian crisis", "references": ["Isaiah 1:1"]},
        {"name": "Jeremiah", "period": "Judah / Babylonian crisis", "references": ["Jeremiah 1:1"]},
        {"name": "Ezekiel", "period": "Exile", "references": ["Ezekiel 1:1"]},
    ],
    "apostles": [
        {"name": "Peter", "roles": ["apostle", "disciple"], "references": ["Matthew 4:18", "Acts 2:14"]},
        {"name": "Andrew", "roles": ["apostle", "disciple"], "references": ["Matthew 4:18"]},
        {"name": "James son of Zebedee", "roles": ["apostle"], "references": ["Matthew 4:21"]},
        {"name": "John", "roles": ["apostle"], "references": ["Matthew 4:21"]},
        {"name": "Philip", "roles": ["apostle"], "references": ["John 1:43"]},
        {"name": "Thomas", "roles": ["apostle"], "references": ["John 20:24"]},
        {"name": "Matthew", "roles": ["apostle"], "references": ["Matthew 9:9"]},
        {"name": "Paul", "roles": ["apostle", "missionary"], "references": ["Acts 9:1", "Romans 1:1"]},
    ],
}
DEFAULT_MAPS = [
    {
        "title": "Canaan and the Patriarchs",
        "period": "Patriarchal narratives",
        "region": "Canaan / Ancient Near East",
        "summary": "Reference map slot for patriarchal journeys and early Genesis locations.",
        "related_passages": ["Genesis 12:1", "Genesis 15:18", "Genesis 21:3"],
        "related_people": ["Abraham", "Sarah", "Isaac", "Jacob"],
        "local_image": "",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Maps_of_ancient_Israel",
        "license": "Curated placeholder; add local public-domain or properly attributed map image.",
        "attribution": "",
    },
    {
        "title": "Exodus and Wilderness",
        "period": "Exodus / wilderness",
        "region": "Egypt, Sinai, Transjordan",
        "summary": "Reference map slot for Exodus route traditions and wilderness narratives.",
        "related_passages": ["Exodus 3:1", "Exodus 12:31", "Numbers 14:25"],
        "related_people": ["Moses", "Aaron", "Miriam"],
        "local_image": "",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Maps_of_the_Exodus",
        "license": "Curated placeholder; add local public-domain or properly attributed map image.",
        "attribution": "",
    },
    {
        "title": "United and Divided Monarchy",
        "period": "United monarchy / divided monarchy",
        "region": "Israel and Judah",
        "summary": "Reference map slot for Saul, David, Solomon, and the later divided kingdoms.",
        "related_passages": ["2 Samuel 5:3", "1 Kings 12:20", "2 Kings 18:1"],
        "related_people": ["Saul", "David", "Solomon", "Hezekiah", "Josiah"],
        "local_image": "",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Maps_of_ancient_Israel",
        "license": "Curated placeholder; add local public-domain or properly attributed map image.",
        "attribution": "",
    },
    {
        "title": "Jerusalem",
        "period": "Biblical and Second Temple periods",
        "region": "Jerusalem",
        "summary": "Reference map slot for Jerusalem, temple, kingship, exile, and Gospel narratives.",
        "related_passages": ["2 Samuel 5:7", "1 Kings 8:1", "Luke 2:22", "John 19:17"],
        "related_people": ["David", "Solomon", "Jesus", "Mary, mother of Jesus"],
        "local_image": "",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Maps_of_Jerusalem",
        "license": "Curated placeholder; add local public-domain or properly attributed map image.",
        "attribution": "",
    },
    {
        "title": "Paul's Journeys",
        "period": "Early church",
        "region": "Eastern Mediterranean",
        "summary": "Reference map slot for Acts and Pauline mission travel.",
        "related_passages": ["Acts 9:1", "Acts 13:4", "Acts 16:9", "Romans 1:1"],
        "related_people": ["Paul", "Barnabas", "Silas", "Timothy", "Luke"],
        "local_image": "",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Maps_of_Paul%27s_missionary_journeys",
        "license": "Curated placeholder; add local public-domain or properly attributed map image.",
        "attribution": "",
    },
]


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
        "â€™": "'",
        "â€œ": '"',
        "â€�": '"',
        "â€˜": "'",
        "â€“": "-",
        "â€”": "-",
        "â†’": "->",
        "â”œâ”€": "-",
        "â””â”€": "-",
        "â”‚": "|",
        "Â": "",
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


def load_themes_data():
    data = read_json(THEMES_DATA_PATH, DEFAULT_THEMES)
    if not isinstance(data, dict):
        return DEFAULT_THEMES
    return {str(theme): [str(ref) for ref in refs] for theme, refs in data.items() if isinstance(refs, list)}


def load_study_data():
    data = read_json(STUDY_DATA_PATH, DEFAULT_STUDY)
    normalized = normalize_study_data(data)
    return normalized or normalize_study_data(DEFAULT_STUDY)


def load_people_data():
    data = read_json(PEOPLE_DATA_PATH, DEFAULT_PEOPLE)
    normalized = normalize_people_data(data)
    if not normalized:
        normalized = normalize_people_data(DEFAULT_PEOPLE)
    return merge_people_profiles(normalized, load_people_text_profiles())


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


def load_people_reference_data():
    data = read_json(PEOPLE_REFERENCE_PATH, DEFAULT_PEOPLE_REFERENCE)
    normalized = normalize_people_reference_data(data)
    return normalized or normalize_people_reference_data(DEFAULT_PEOPLE_REFERENCE)


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


def load_maps_data():
    data = read_json(MAPS_DATA_PATH, DEFAULT_MAPS)
    normalized = normalize_maps_data(data)
    return merge_discovered_maps(normalized or normalize_maps_data(DEFAULT_MAPS), discover_map_assets())


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


from bible_app.core.maps import (  # noqa: E402
    discover_map_assets,
    infer_map_metadata,
    map_match_key,
    map_title_from_path,
    map_titles_are_related,
    merge_discovered_maps,
    preferred_map_asset_title,
    resolve_local_map_image,
)
from bible_app.core.study_tools import (  # noqa: E402
    clean_imported_text,
    infer_person_canon,
    infer_person_category,
    load_people_text_profiles,
    merge_people_profiles,
    normalize_maps_data,
    normalize_people_data,
    normalize_people_reference_data,
    normalize_reference_collection,
    normalize_study_data,
    parse_people_text_file,
    person_name_from_filename,
    references_from_text,
)


def read_json(path, fallback):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    return fallback


def backup_file(path):
    if not path.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"{path.stem}-{timestamp}{path.suffix}"
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def write_json(path, payload, make_backup=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    if make_backup:
        backup_file(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


from bible_app.storage.backup import BackupManager, backup_file  # noqa: E402
from bible_app.storage.data_manager import read_json, write_json  # noqa: E402


def read_notes():
    return read_json(NOTES_PATH, {})


def write_notes(notes):
    write_json(NOTES_PATH, notes)


def read_journal():
    return read_json(JOURNAL_PATH, [])


def write_journal(entries):
    write_json(JOURNAL_PATH, entries)


def read_bookmarks():
    return read_json(BOOKMARKS_PATH, [])


def write_bookmarks(bookmarks):
    write_json(BOOKMARKS_PATH, bookmarks)


def read_highlights():
    return read_json(HIGHLIGHTS_PATH, {})


def write_highlights(highlights):
    write_json(HIGHLIGHTS_PATH, highlights)


def normalize_concepts(data):
    if not isinstance(data, list):
        data = DEFAULT_CONCEPTS
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


def read_concepts():
    return normalize_concepts(read_json(CONCEPTS_PATH, DEFAULT_CONCEPTS))


def write_concepts(concepts):
    write_json(CONCEPTS_PATH, normalize_concepts(concepts))


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
            "created": str(item.get("created", datetime.now().isoformat(timespec="seconds"))),
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
    return [
        {"name": "Gospels in 30 Days", "references": [f"{book} {chapter}" for book in ("Matthew", "Mark", "Luke", "John") for chapter in range(1, BOOK_CHAPTERS[book] + 1)], "completed": []},
        {"name": "Psalms", "references": [f"Psalm {chapter}" for chapter in range(1, BOOK_CHAPTERS["Psalm"] + 1)], "completed": []},
        {"name": "New Testament Overview", "references": [f"{book} {chapter}" for book in BOOK_ORDER[39:] for chapter in range(1, BOOK_CHAPTERS[book] + 1)], "completed": []},
    ]


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
    return normalize_reading_plans(read_json(READING_PLANS_PATH, default_reading_plans()))


def write_reading_plans(plans):
    write_json(READING_PLANS_PATH, normalize_reading_plans(plans))


WORKSHEET_FIELDS = ["observation", "interpretation", "application", "questions", "prayer", "related_hymn", "tags"]


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
                    "linked": str(item.get("linked", datetime.now().isoformat(timespec="seconds"))),
                })
        if clean_items:
            links[str(ref)] = clean_items
    return links


def read_hymn_links():
    return normalize_hymn_links(read_json(HYMN_LINKS_PATH, {}))


def write_hymn_links(links):
    write_json(HYMN_LINKS_PATH, normalize_hymn_links(links))


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
            "added": str(item.get("added", datetime.now().isoformat(timespec="seconds"))),
        })
    return items


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
            "opened": str(item.get("opened", datetime.now().isoformat(timespec="seconds")) if isinstance(item, dict) else datetime.now().isoformat(timespec="seconds")),
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


from bible_app.storage.user_data import (  # noqa: E402
    WORKSHEET_FIELDS,
    default_reading_plans,
    normalize_concepts,
    normalize_hymn_collection,
    normalize_hymn_links,
    normalize_reading_plans,
    normalize_recent_references,
    normalize_study_sessions,
    normalize_user_cross_references,
    normalize_worksheets,
    read_bookmarks,
    read_concepts,
    read_highlights,
    read_hymn_favorites,
    read_hymn_links,
    read_journal,
    read_notes,
    read_reading_plans,
    read_recent_hymns,
    read_recent_references,
    read_study_sessions,
    read_user_cross_references,
    read_worksheets,
    write_bookmarks,
    write_concepts,
    write_highlights,
    write_hymn_favorites,
    write_hymn_links,
    write_journal,
    write_notes,
    write_reading_plans,
    write_recent_hymns,
    write_recent_references,
    write_study_sessions,
    write_user_cross_references,
    write_worksheets,
)


def normalize_document_library(data):
    if not isinstance(data, list):
        return []
    documents = []
    for item in data:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        if not doc_id or not title:
            continue
        documents.append({
            "id": doc_id,
            "title": title,
            "source_path": str(item.get("source_path", "")),
            "created": str(item.get("created", "")),
            "type": str(item.get("type", "")),
            "text": str(item.get("text", "")),
            "images": [str(path) for path in item.get("images", []) if str(path).strip()],
        })
    return documents


def read_document_library():
    return normalize_document_library(read_json(DOCUMENT_LIBRARY_PATH, []))


def write_document_library(documents):
    write_json(DOCUMENT_LIBRARY_PATH, normalize_document_library(documents))


def safe_document_id(title):
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", title).strip("-") or "document"
    return f"{base}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def extract_docx_text_and_images(path, image_dir):
    text_parts = []
    images = []
    try:
        import zipfile
        from xml.etree import ElementTree

        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" in archive.namelist():
                tree = ElementTree.fromstring(archive.read("word/document.xml"))
                namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                text_parts = [node.text or "" for node in tree.findall(".//w:t", namespace)]
            for name in archive.namelist():
                if name.startswith("word/media/"):
                    target = image_dir / Path(name).name
                    target.write_bytes(archive.read(name))
                    images.append(str(target))
    except Exception as exc:
        raise RuntimeError(f"Could not read DOCX file: {exc}") from exc
    return "\n".join(part for part in text_parts if part).strip(), images


def extract_pdf_text_and_images(path, image_dir):
    text = ""
    images = []
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception as exc:
            raise RuntimeError(f"Could not extract PDF text. Install pypdf for PDF conversion. Details: {exc}") from exc

    try:
        import fitz

        doc = fitz.open(str(path))
        for page_index in range(len(doc)):
            for image_index, image in enumerate(doc[page_index].get_images(full=True), 1):
                xref = image[0]
                payload = doc.extract_image(xref)
                ext = payload.get("ext", "png")
                target = image_dir / f"page-{page_index + 1}-image-{image_index}.{ext}"
                target.write_bytes(payload["image"])
                images.append(str(target))
    except Exception:
        pass
    return text, images


def pdf_reader_for(path):
    try:
        from pypdf import PdfReader

        return PdfReader(str(path))
    except Exception:
        try:
            from PyPDF2 import PdfReader

            return PdfReader(str(path))
        except Exception as exc:
            raise RuntimeError(f"Could not read PDF. Install pypdf for PDF support. Details: {exc}") from exc


def clean_hymn_text(text):
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "’": "'",
        "“": '"',
        "”": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def parse_hymn_header(header):
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
    if not HYMNALS_DIR.exists():
        return []
    return sorted(path for path in HYMNALS_DIR.glob("*.pdf") if path.is_file())


def build_hymnal_index(path):
    reader = pdf_reader_for(path)
    hymns = []
    for page_index, page in enumerate(reader.pages):
        try:
            item = parse_hymn_page(page.extract_text() or "", page_index + 1)
        except Exception:
            item = None
        if item:
            item["file"] = str(path)
            hymns.append(item)
    return hymns


def hymnal_cache_key(path):
    try:
        return str(Path(path).resolve())
    except Exception:
        return str(path)


def hymnal_cache_metadata(path):
    source = Path(path)
    stat = source.stat()
    return {
        "path": hymnal_cache_key(source),
        "size": stat.st_size,
        "mtime_ns": getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
    }


def cached_hymnal_entry_is_valid(path, entry):
    if not isinstance(entry, dict):
        return False
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        return False
    try:
        current = hymnal_cache_metadata(path)
    except Exception:
        return False
    return (
        metadata.get("path") == current["path"]
        and metadata.get("size") == current["size"]
        and metadata.get("mtime_ns") == current["mtime_ns"]
        and isinstance(entry.get("hymns"), list)
    )


def read_hymnal_index_cache():
    data = read_json(HYMNAL_INDEX_CACHE_PATH, {})
    return data if isinstance(data, dict) else {}


def write_hymnal_index_cache(cache):
    write_json(HYMNAL_INDEX_CACHE_PATH, cache)


def read_cached_hymnal_index(path):
    cache = read_hymnal_index_cache()
    entry = cache.get(hymnal_cache_key(path))
    if cached_hymnal_entry_is_valid(path, entry):
        return entry.get("hymns", [])
    return None


def write_cached_hymnal_index(path, hymns):
    cache = read_hymnal_index_cache()
    key = hymnal_cache_key(path)
    cache[key] = {
        "metadata": hymnal_cache_metadata(path),
        "created": datetime.now().isoformat(timespec="seconds"),
        "hymns": hymns,
    }
    write_hymnal_index_cache(cache)


def load_hymnal_index(path):
    cached = read_cached_hymnal_index(path)
    if cached is not None:
        return cached, True
    hymns = build_hymnal_index(path)
    write_cached_hymnal_index(path, hymns)
    return hymns, False


def render_pdf_page_image(path, page_number, zoom=1.35):
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
    except Exception:
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


from bible_app.core.hymns import (  # noqa: E402
    build_hymnal_index,
    cached_hymnal_entry_is_valid,
    clean_hymn_text,
    hymnal_cache_key,
    hymnal_cache_metadata,
    hymnal_files,
    load_hymnal_index,
    looks_like_hymn_page,
    parse_hymn_header,
    parse_hymn_page,
    pdf_reader_for,
    read_cached_hymnal_index,
    read_hymnal_index_cache,
    render_pdf_page_image,
    write_cached_hymnal_index,
    write_hymnal_index_cache,
)


def convert_document_to_library_item(path, title=None, progress=None):
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    title = (title or source.stem).strip() or source.stem
    doc_id = safe_document_id(title)
    image_dir = DOCUMENT_IMAGE_DIR / doc_id
    image_dir.mkdir(parents=True, exist_ok=True)

    def report(value, message):
        if progress:
            progress(value, message)

    report(10, "Reading document...")
    ext = source.suffix.lower()
    images = []
    if ext == ".pdf":
        text, images = extract_pdf_text_and_images(source, image_dir)
    elif ext == ".docx":
        text, images = extract_docx_text_and_images(source, image_dir)
    elif ext in {".txt", ".md"}:
        text = source.read_text(encoding="utf-8", errors="ignore")
    elif ext in {".html", ".htm"}:
        raw = source.read_text(encoding="utf-8", errors="ignore")
        parser = PlainTextHTMLParser()
        parser.feed(raw)
        text = parser.text()
    else:
        raise RuntimeError("Supported document types: PDF, DOCX, TXT, MD, HTML.")

    report(70, "Saving converted JSON...")
    item = {
        "id": doc_id,
        "title": title,
        "source_path": str(source),
        "created": datetime.now().isoformat(timespec="seconds"),
        "type": ext.lstrip("."),
        "text": text.strip(),
        "images": images,
    }
    documents = read_document_library()
    documents.append(item)
    write_document_library(documents)
    report(100, "Conversion complete.")
    return item


def matching_document_for_source(documents, source_path):
    source = str(Path(source_path).resolve()).lower()
    for item in documents:
        item_source = str(item.get("source_path", "")).strip()
        if item_source and str(Path(item_source).resolve()).lower() == source:
            return item
    return None


from bible_app.core.documents import (  # noqa: E402
    PlainTextHTMLParser,
    convert_document_to_library_item,
    extract_docx_text_and_images,
    extract_pdf_text_and_images,
    matching_document_for_source,
    normalize_document_library,
    read_document_library,
    safe_document_id,
    write_document_library,
)


def ensure_niv_pdf_document(progress=None):
    if not NIV_PDF_PATH.exists():
        raise FileNotFoundError(NIV_PDF_PATH)
    documents = read_document_library()
    existing = matching_document_for_source(documents, NIV_PDF_PATH)
    if existing:
        return existing, False
    item = convert_document_to_library_item(NIV_PDF_PATH, "NIV Bible PDF", progress=progress)
    return item, True


def read_settings():
    return read_json(SETTINGS_PATH, {
        "reader_bg": "#fbfcfd",
        "reader_fg": "#1F1F1F",
        "highlight_bg": "#edf6f5",
        "reader_font": "Georgia",
        "reader_font_size": 13,
    })


def write_settings(settings):
    write_json(SETTINGS_PATH, settings)


def normalize_bible_data(data):
    normalized = {}
    if not isinstance(data, dict):
        return normalized
    for translation, books in data.items():
        if not isinstance(books, dict):
            continue
        normalized[translation] = {}
        for book, chapters in books.items():
            if not isinstance(chapters, dict):
                continue
            normalized[translation][book] = {}
            for chapter, verses in chapters.items():
                try:
                    chapter_number = int(chapter)
                except Exception:
                    continue
                if isinstance(verses, list):
                    normalized[translation][book][chapter_number] = [str(verse).strip() for verse in verses]
    return normalized


def bundled_translation_code(metadata, fallback):
    raw = str(metadata.get("shortname") or fallback).strip()
    code = re.sub(r"[^A-Za-z0-9]+", "", raw).upper()
    if code == "KJV":
        return "KJV"
    return code or fallback.upper()


def normalize_bundled_bible_file(path):
    payload = read_json(path, {})
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    verses = payload.get("verses", []) if isinstance(payload, dict) else []
    if not isinstance(metadata, dict) or not isinstance(verses, list):
        return None, None, {}
    if metadata.get("restrict", 1):
        return None, None, {}
    code = bundled_translation_code(metadata, path.stem)
    label = str(metadata.get("name") or metadata.get("shortname") or path.stem)
    translation = {}
    for item in verses:
        if not isinstance(item, dict):
            continue
        book = canonical_book_name(item.get("book_name", ""))
        if not book:
            continue
        try:
            chapter = int(item.get("chapter"))
            verse = int(item.get("verse"))
        except Exception:
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        chapter_verses = translation.setdefault(book, {}).setdefault(chapter, [])
        while len(chapter_verses) < verse:
            chapter_verses.append("")
        chapter_verses[verse - 1] = text
    return code, label, translation


def load_bundled_translations():
    translations = {}
    labels = {}
    if not BUNDLED_ENGLISH_DIR.exists():
        return translations, labels
    for path in sorted(BUNDLED_ENGLISH_DIR.glob("*.json")):
        code, label, translation = normalize_bundled_bible_file(path)
        if code and translation:
            translations[code] = translation
            labels[code] = label
    return translations, labels


def bundled_translation_for(code):
    translations, labels = load_bundled_translations()
    key = str(code).upper()
    return translations.get(key), labels.get(key, key)


def canonical_book_name(book):
    compact = re.sub(r"\s+", " ", str(book).strip()).lower()
    squashed = compact.replace(" ", "")
    return BOOK_ALIASES.get(compact) or BOOK_ALIASES.get(squashed)


def reference_parts(ref):
    match = re.match(r"^(.+?)\s+(\d+)(?::(\d+))?$", ref.strip())
    if not match:
        return None
    book = canonical_book_name(match.group(1))
    if not book:
        return None
    return book, int(match.group(2)), int(match.group(3) or 1)


def reference_range_parts(ref):
    match = re.match(r"^(.+?)\s+(\d+):(\d+)\s*-\s*(\d+)$", ref.strip())
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
    return reference_range_parts(ref) is not None


def normalized_reference(ref):
    range_parts = reference_range_parts(ref)
    if range_parts:
        book, chapter, start, end = range_parts
        return f"{book} {chapter}:{start}-{end}"
    parts = reference_parts(ref)
    if parts:
        book, chapter, verse = parts
        return f"{book} {chapter}:{verse}"
    return str(ref).strip()


def markdown_line(value):
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n")


def word_occurrences(translation_data, query):
    query = str(query or "").strip()
    if not query:
        return []

    matches = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for book, chapters in translation_data.items():
        for chapter, verses in chapters.items():
            for verse_num, verse_text in enumerate(verses, 1):
                verse_matches = pattern.findall(verse_text)
                if verse_matches:
                    ref = f"{book} {chapter}:{verse_num}"
                    matches.append({
                        "reference": ref,
                        "text": verse_text,
                        "count": len(verse_matches),
                    })
    return matches


def verse_text_from_translation(translation_code, ref):
    parts = reference_parts(ref)
    if not parts:
        return ""

    book, chapter, verse = parts
    verses = BIBLE.get(translation_code, {}).get(book, {}).get(chapter, [])
    if verse <= 0 or verse > len(verses):
        return ""
    return verses[verse - 1]


def niv_chapter_segments(text):
    text = str(text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<!\d)(\d{1,3})(?=[A-Za-z\"'(\u201c])", text)
    segments = []
    first = parts[0].strip()
    if first:
        segments.append((1, first))
    for index in range(1, len(parts), 2):
        try:
            verse_number = int(parts[index])
        except Exception:
            continue
        verse_text = parts[index + 1].strip() if index + 1 < len(parts) else ""
        if verse_text:
            segments.append((verse_number, verse_text))
    if not segments:
        return [(1, text)]
    return segments


def format_niv_chapter_text(text):
    return "\n\n".join(f"{number}. {verse}" for number, verse in niv_chapter_segments(text))


from bible_app.core.translations import (  # noqa: E402
    bible_text_has_web_noise,
    bundled_translation_code,
    bundled_translation_for,
    format_niv_chapter_text,
    load_bundled_translations,
    niv_chapter_segments,
    normalize_bible_data,
    normalize_bundled_bible_file,
    restore_cached_translations,
)


def reference_sort_key(ref):
    parts = reference_parts(ref)
    if not parts:
        return (999, 999, 999)
    book, chapter, verse = parts
    try:
        book_index = BOOK_ORDER.index(book)
    except ValueError:
        book_index = 998
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

    results = []
    for book, chapters in translation_data.items():
        if books is not None and book not in books:
            continue
        for chapter, verses in chapters.items():
            for verse_num, verse_text in enumerate(verses, 1):
                matches = list(pattern.finditer(verse_text))
                if not matches:
                    continue
                ref = f"{book} {chapter}:{verse_num}"
                preview = verse_text
                if context and matches:
                    start = max(0, matches[0].start() - 45)
                    end = min(len(verse_text), matches[0].end() + 70)
                    preview = ("..." if start else "") + verse_text[start:end] + ("..." if end < len(verse_text) else "")
                results.append({
                    "reference": ref,
                    "text": verse_text,
                    "preview": preview,
                    "count": len(matches),
                })

    if sort_mode == "Relevance":
        results.sort(key=lambda item: (-item["count"], reference_sort_key(item["reference"])))
    else:
        results.sort(key=lambda item: reference_sort_key(item["reference"]))
    return results


from bible_app.core.references import (  # noqa: E402
    canonical_book_name,
    is_range_reference,
    normalized_reference,
    reference_parts,
    reference_range_parts,
)
from bible_app.core.search import (  # noqa: E402
    reference_sort_key,
    search_bible,
    word_occurrences,
)


def commentary_candidates(ref):
    parts = reference_parts(ref)
    if not parts:
        return []
    book, chapter, verse = parts
    return [
        COMMENTARY_DIR / f"{book} {chapter} {verse}.md",
        COMMENTARY_DIR / f"{book} {chapter}-{verse}.md",
        COMMENTARY_DIR / f"{book} {chapter}.md",
        COMMENTARY_DIR / f"{book}.md",
    ]


def commentary_for_reference(ref):
    for path in commentary_candidates(ref):
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore").strip(), path
    return "", None


def refs_for_study_entry(ref):
    range_parts = reference_range_parts(ref)
    if range_parts:
        book, chapter, start, end = range_parts
        return [f"{book} {chapter}:{verse}" for verse in range(start, end + 1)]
    return [normalized_reference(ref)]


def themes_for_reference(ref):
    refs = set(refs_for_study_entry(ref))
    return sorted(theme for theme, theme_refs in THEMES.items() if refs.intersection(theme_refs))


def cross_reference_edges(ref):
    edges = []
    seen = set()
    for source in refs_for_study_entry(ref):
        for target in STUDY.get(source, {}).get("cross", []):
            edge = (source, normalized_reference(target))
            if edge not in seen:
                edges.append(edge)
                seen.add(edge)
    return edges


def strongs_text_for_reference(ref):
    parts = reference_parts(ref)
    if not parts:
        return ""
    book, chapter, verse = parts
    path = BUNDLED_ENGLISH_DIR / "kjv_strongs.json"
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    for item in payload.get("verses", []):
        if item.get("book_name") == book and int(item.get("chapter", 0)) == chapter and int(item.get("verse", 0)) == verse:
            return str(item.get("text", ""))
    return ""


def original_language_warnings():
    seen = {}
    warnings = []
    for entry in STUDY.values():
        for word, original, _note in entry.get("language", []):
            key = str(word).lower()
            seen.setdefault(key, set()).add(str(original))
    for word, originals in sorted(seen.items()):
        if len(originals) > 1:
            warnings.append(f"{word}: " + ", ".join(sorted(originals)))
    return warnings


def searchable_map_text(map_item):
    return " ".join([
        map_item.get("title", ""),
        map_item.get("period", ""),
        map_item.get("region", ""),
        map_item.get("summary", ""),
        " ".join(map_item.get("related_people", [])),
        " ".join(map_item.get("related_places", [])),
        " ".join(map_item.get("related_passages", [])),
    ]).lower()


def reference_scope(ref):
    range_parts = reference_range_parts(ref)
    if range_parts:
        return range_parts
    parts = reference_parts(ref)
    if not parts:
        return None
    book, chapter, verse = parts
    return book, chapter, verse, verse


def study_entries_for_reference(ref):
    exact_ref = normalized_reference(ref)
    entries = []
    exact_entry = STUDY.get(exact_ref)
    if exact_entry:
        entries.append((exact_ref, exact_entry, 3))

    scope = reference_scope(exact_ref)
    if not scope:
        return entries
    book, chapter, start_verse, end_verse = scope

    for study_ref, entry in STUDY.items():
        if study_ref == exact_ref:
            continue
        parts = reference_parts(study_ref)
        if not parts:
            continue
        study_book, study_chapter, study_verse = parts
        if study_book != book or study_chapter != chapter:
            continue
        weight = 2 if start_verse <= study_verse <= end_verse else 1
        entries.append((study_ref, entry, weight))
    return entries


def maps_for_reference(ref):
    scope = reference_scope(ref)
    study_entries = study_entries_for_reference(ref)
    refs = set(refs_for_study_entry(ref))
    people = set()
    places = set()
    map_note_parts = []
    for study_ref, entry, _weight in study_entries:
        refs.add(study_ref)
        people.update(entry.get("people", []))
        places.update(place.lower() for place in entry.get("places", []))
        if entry.get("map"):
            map_note_parts.append(entry.get("map", ""))
    map_note = " ".join(map_note_parts).lower()
    book = scope[0] if scope else ""
    chapter = scope[1] if scope else None
    matches = []
    for map_item in MAPS:
        score = 0
        map_refs = set(map_item.get("related_passages", []))
        if refs.intersection(map_refs):
            score += 8
        elif book and chapter:
            for map_ref in map_refs:
                map_parts = reference_parts(map_ref)
                if map_parts and map_parts[0] == book and map_parts[1] == chapter:
                    score += 4
                    break
        if people.intersection(map_item.get("related_people", [])):
            score += 5
        map_places = {place.lower() for place in map_item.get("related_places", [])}
        if places.intersection(map_places):
            score += 5
        search_text = searchable_map_text(map_item)
        for place in places:
            if place and place in search_text:
                score += 4
        if book and book.lower() in search_text:
            score += 2
        for token in re.findall(r"[A-Za-z]{4,}", map_note):
            if token.lower() in search_text:
                score += 1
        if score:
            item = dict(map_item)
            item["_score"] = score
            matches.append(item)
    matches.sort(key=lambda item: (-item["_score"], item.get("title", "")))
    return matches


def maps_for_person(name):
    matches = []
    for map_item in MAPS:
        if name in map_item.get("related_people", []):
            item = dict(map_item)
            item["_score"] = 5
            matches.append(item)
            continue
        if name.lower() in searchable_map_text(map_item):
            item = dict(map_item)
            item["_score"] = 2
            matches.append(item)
    matches.sort(key=lambda item: (-item["_score"], item.get("title", "")))
    return matches


THEMES = load_themes_data()
STUDY = load_study_data()
PEOPLE = load_people_data()
PEOPLE_REFERENCE = load_people_reference_data()
MAPS = load_maps_data()


def sample_bible():
    return json.loads(json.dumps(BIBLE))


def load_bible_library():
    global BUNDLED_TRANSLATION_LABELS
    bundled_translations, BUNDLED_TRANSLATION_LABELS = load_bundled_translations()
    library = normalize_bible_data(sample_bible())
    library.update(bundled_translations)
    label = "KJV sample"
    if BIBLE_DATA_PATH.exists():
        try:
            raw_text = BIBLE_DATA_PATH.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            has_web_noise = bible_text_has_web_noise(raw_text)
            if isinstance(data, dict) and data.get("translations"):
                translations = normalize_bible_data(data["translations"]) if has_web_noise else restore_cached_translations(data["translations"])
                library.update(translations)
                if has_web_noise:
                    logger.warning("Repairing Bible cache after removing source-page script text.")
                    try:
                        write_json(BIBLE_DATA_PATH, {"label": data.get("label", "KJV local"), "source": "local cache", "translations": library})
                    except Exception as exc:
                        logger.warning("Could not rewrite repaired Bible cache yet: %s", exc)
                return library, data.get("label", "KJV local")
            if isinstance(data, dict) and "KJV" in data:
                translations = normalize_bible_data(data) if has_web_noise else restore_cached_translations(data)
                library.update(translations)
                if has_web_noise:
                    logger.warning("Repairing Bible cache after removing source-page script text.")
                    try:
                        write_json(BIBLE_DATA_PATH, {"label": "KJV local", "source": "local cache", "translations": library})
                    except Exception as exc:
                        logger.warning("Could not rewrite repaired Bible cache yet: %s", exc)
                return library, "KJV local"
        except Exception as exc:
            logger.warning("Could not load local Bible library from %s; using starter library. Error: %s", BIBLE_DATA_PATH, exc)
    return library, label


def save_bible_library(label="KJV local cache"):
    write_json(BIBLE_DATA_PATH, {"label": label, "source": "local cache", "translations": BIBLE})


class PlainTextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        data = data.strip()
        if data:
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def fetch_kjv_chapter(book, chapter):
    reference = urllib.parse.quote(f"{book} {chapter}")
    url = BIBLE_API_URL.format(reference=reference)
    request = urllib.request.Request(url, headers={"User-Agent": "BibleReferenceStudyTool/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    verses = payload.get("verses", [])
    if not verses:
        raise RuntimeError(f"No verses returned for {book} {chapter}.")
    verses.sort(key=lambda item: int(item.get("verse", 0)))
    return [item.get("text", "").strip() for item in verses]


def parse_numbered_chapter_text(text):
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
        if verse:
            verses.append(verse)
    return verses


def fetch_jps_chapter(book, chapter):
    code = JPS_BOOK_CODES.get(book)
    if not code:
        raise RuntimeError(f"{book} is not part of the JPS 1917 Hebrew Bible.")
    url = JPS_BASE_URL.format(code=code, chapter=chapter)
    request = urllib.request.Request(url, headers={"User-Agent": "BibleReferenceStudyTool/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", "ignore")
    parser = PlainTextHTMLParser()
    parser.feed(html)
    verses = parse_numbered_chapter_text(parser.text())
    if not verses:
        raise RuntimeError(f"No verses returned for {book} {chapter}.")
    return verses


def fetch_translation_chapter(translation, book, chapter):
    if translation == "KJV":
        return fetch_kjv_chapter(book, chapter)
    if translation == "JPS1917":
        return fetch_jps_chapter(book, chapter)
    raise RuntimeError(f"{translation} chapters cannot be fetched online automatically.")


from bible_app.core.bible_data import (  # noqa: E402
    fetch_url,
    fetch_jps_chapter,
    fetch_kjv_chapter,
    fetch_translation_chapter,
    parse_numbered_chapter_text,
)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=118, height=30, radius=9):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=APP_PANEL,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.radius = radius
        self.normal_fill = "#F4F6F8"
        self.hover_fill = "#E8F2FC"
        self.press_fill = "#D7EAFB"
        self.border = "#C8D0D8"
        self.text_color = "#1F1F1F"
        self.fill = self.normal_fill
        self.draw()
        self.bind("<Enter>", lambda _event: self.set_fill(self.hover_fill))
        self.bind("<Leave>", lambda _event: self.set_fill(self.normal_fill))
        self.bind("<ButtonPress-1>", lambda _event: self.set_fill(self.press_fill))
        self.bind("<ButtonRelease-1>", self.on_release)

    def draw(self):
        self.delete("all")
        r = self.radius
        w = self.width
        h = self.height
        points = [
            r, 1, w - r, 1, w - r, 1, w - 1, 1, w - 1, r,
            w - 1, h - r, w - 1, h - r, w - 1, h - 1, w - r, h - 1,
            r, h - 1, r, h - 1, 1, h - 1, 1, h - r,
            1, r, 1, r, 1, 1, r, 1,
        ]
        self.create_polygon(points, smooth=True, fill=self.fill, outline=self.border)
        self.create_text(w / 2, h / 2, text=self.text, fill=self.text_color, font=("Segoe UI", 9))

    def set_fill(self, fill):
        self.fill = fill
        self.draw()

    def on_release(self, event):
        self.set_fill(self.hover_fill)
        if 0 <= event.x <= self.width and 0 <= event.y <= self.height:
            self.command()


class BibleReferenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        logger.info("Starting Bible Reference Study Tool")
        self.title(APP_SETTINGS.app_title)
        self.geometry(APP_SETTINGS.window_geometry)
        self.minsize(*APP_SETTINGS.min_window_size)
        global BIBLE
        BIBLE, self.library_label = load_bible_library()
        logger.info("Loaded Bible library: %s translations, label=%s", len(BIBLE), self.library_label)
        self.translation = DEFAULT_TRANSLATION if DEFAULT_TRANSLATION in BIBLE else ("KJV" if "KJV" in BIBLE else next(iter(BIBLE), "KJV"))
        self.current_book, self.current_chapter, first_verse = self.first_available_reference()
        self.selected_ref = f"{self.current_book} {self.current_chapter}:{first_verse}"
        self.notes = read_notes()
        self.journal_entries = read_journal()
        self.bookmarks = read_bookmarks()
        self.highlights = read_highlights()
        self.concepts = read_concepts(DEFAULT_CONCEPTS)
        self.study_sessions = read_study_sessions()
        self.reading_plans = read_reading_plans()
        self.worksheets = read_worksheets()
        self.hymn_links = read_hymn_links()
        self.hymn_favorites = read_hymn_favorites()
        self.recent_hymns = read_recent_hymns()
        self.recent_references = read_recent_references()
        self.user_cross_references = read_user_cross_references()
        self.library_documents = read_document_library()
        self.settings = read_settings()
        
        # New features data structures
        self.verse_highlights = {}  # Format: {"John 3:16": {"color": "#ffff00", "category": "Important"}}
        self.verse_tags = {}  # Format: {"John 3:16": ["Salvation", "Love"]}
        self.reading_history = []  # Format: [{"reference": "John 3:16", "date": "2024-01-01", "time_spent": 120}]
        self.statistics = {
            "total_verses_read": 0,
            "total_reading_time": 0,
            "highlighted_verses": 0,
            "tagged_verses": 0,
            "most_highlighted": [],
            "most_tagged": [],
        }
        self.highlight_categories = {
            "#ffff00": "Important",
            "#ff9999": "Questions",
            "#99ccff": "Promises",
            "#99ff99": "Commands",
            "#ffcc99": "Prophecy",
        }
        
        self.back_stack = []
        self.forward_stack = []
        self.autosave_after_id = None
        self.loading_note = False
        self.download_busy = False
        self.niv_pdf_import_busy = False
        self.hymnal_index_cache = {}
        self.fetching_chapters = set()
        self.lookup_cache = BibleLookupCache(PASSAGE_CACHE_SIZE)
        self.background = BackgroundTaskRunner(self)
        self.app_status_var = tk.StringVar(value=f"Loaded: {self.library_label}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_style()
        self.build_ui()
        self.render_all()
        self.select_verse(self.selected_ref, rerender=False)
        if AUTO_BACKUP_ON_STARTUP:
            self.after(2000, self.create_startup_backup_async)
        self.after(400, self.check_connection_async)
        self.after(1200, self.ensure_niv_pdf_in_background)

    def on_close(self):
        try:
            self.background.shutdown()
        finally:
            self.destroy()

    def create_startup_backup(self):
        try:
            backup_path = BackupManager(BACKUP_DIR, max_backups=MAX_BACKUPS).create_backup(USER_DATA_DIR)
            if backup_path:
                logger.info("Startup data backup created: %s", backup_path)
        except Exception as exc:
            logger.exception("Startup data backup failed: %s", exc)

    def create_startup_backup_async(self):
        try:
            self.background.submit(self.create_startup_backup)
            self.app_status_var.set("Startup backup is running in the background.")
        except Exception as exc:
            logger.exception("Could not start background startup backup: %s", exc)

    def create_rounded_button_styles(self, style):
        # Tk's built-in ttk button text rendering is more reliable than
        # image-backed layouts across Windows/Python builds. The dedicated
        # local-library RoundedButton canvas still gives that section true
        # rounded corners, while global ttk buttons keep visible labels.
        return

    def build_style(self):
        """Apply Windows 11 Fluent Design styling."""
        style = configure_app_styles(self)
        self.create_rounded_button_styles(style)

    def create_tool_menu(self, parent, label, items):
        button = ttk.Menubutton(parent, text=label, style="Tool.TMenubutton")
        menu = tk.Menu(button, tearoff=False)
        for item_label, command in items:
            if item_label == "-":
                menu.add_separator()
            else:
                menu.add_command(label=item_label, command=command)
        button.configure(menu=menu)
        button.pack(side="left", padx=(0, 6))
        return button

    def build_ui(self):
        header = ttk.Frame(self, padding=(14, 12))
        header.pack(fill="x")
        nav = ttk.Frame(header)
        nav.pack(side="left", padx=(0, 10))
        self.back_button = ttk.Button(nav, text="Back", command=self.go_back, state="disabled")
        self.back_button.pack(side="left")
        self.forward_button = ttk.Button(nav, text="Forward", command=self.go_forward, state="disabled")
        self.forward_button.pack(side="left", padx=(6, 0))
        title_box = ttk.Frame(header)
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="Bible Reference Study Tool", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="Desktop prototype: reader, concordance, themes, maps, and notes", style="Muted.TLabel").pack(anchor="w")
        lookup = ttk.Frame(header)
        lookup.pack(side="right", fill="x")
        self.lookup_var = tk.StringVar()
        entry = ttk.Entry(lookup, textvariable=self.lookup_var, width=38)
        entry.pack(side="left", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self.open_lookup())
        ttk.Button(lookup, text="Open Passage", command=self.open_lookup, style="Primary.TButton").pack(side="left")
        ttk.Button(lookup, text="Setup", command=self.open_settings_window).pack(side="left", padx=(8, 0))
        
        tools = ttk.Frame(header, style="Toolbar.TFrame")
        tools.pack(side="right", fill="x", padx=(8, 0))
        self.create_tool_menu(tools, "Study", [
            ("Home Dashboard", self.open_study_dashboard),
            ("Passage Worksheet", self.open_study_worksheet),
            ("Save Web Commentary", self.open_web_commentary_importer),
            ("Study Binder", self.open_study_binder),
            ("Study Sessions", self.open_study_sessions_window),
            ("Reading Plans", self.open_reading_plans_window),
        ])
        self.create_tool_menu(tools, "Search", [
            ("Search Everything", self.open_search_everything),
            ("Word Study", self.open_word_study_window),
            ("Compare Translations", self.open_translation_comparison_window),
            ("Verse Statistics", self.show_verse_statistics),
        ])
        self.create_tool_menu(tools, "Explore", [
            ("Timeline", self.open_timeline_window),
            ("Cross Reference Graph", self.open_cross_reference_graph),
            ("Presentation Mode", self.open_presentation_mode),
        ])
        self.create_tool_menu(tools, "Manage", [
            ("Tags", self.open_tag_window),
            ("Export Study Packet", self.export_study_packet),
            ("Settings", self.open_settings_window),
        ])
        self.create_tool_menu(tools, "Help", [
            ("Open Help", self.open_help_window),
            ("Reference Guide", lambda: self.open_help_document("REFERENCE_GUIDE.md")),
            ("Developer Guide", lambda: self.open_help_document("DEVELOPERS_GUIDE.md")),
        ])

        status_bar = ttk.Frame(self, style="Status.TFrame", padding=(12, 5))
        status_bar.pack(side="bottom", fill="x")
        ttk.Label(status_bar, textvariable=self.app_status_var, style="Status.TLabel").pack(side="left", fill="x", expand=True)

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=10)
        center = ttk.Frame(body, padding=12)
        right = ttk.Frame(body, padding=10)
        self.color_frames = [header, nav, title_box, lookup, left, center, right]
        self.body_pane = body
        body.add(left, weight=1)
        body.add(center, weight=4)
        body.add(right, weight=2)

        self.build_left(left)
        self.build_center(center)
        self.build_right(right)
        self.after_idle(self.set_initial_pane_sizes)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def set_initial_pane_sizes(self):
        width = self.body_pane.winfo_width()
        if width < 900:
            return
        try:
            self.body_pane.sashpos(0, 300)
            self.body_pane.sashpos(1, max(620, width - 360))
        except tk.TclError:
            pass

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        self.bind("<Control-f>", lambda e: self.search_word())  # Ctrl+F for search
        self.bind("<Control-b>", lambda e: self.add_bookmark())  # Ctrl+B for bookmark
        self.bind("<Control-n>", lambda e: self.open_journal_window())  # Ctrl+N for note/journal
        self.bind("<Control-d>", lambda e: self.open_settings_window())  # Ctrl+D for settings
        self.bind("<Control-t>", lambda e: self.open_tag_window())  # Ctrl+T for tags
        self.bind("<Control-w>", lambda e: self.open_word_study_window())  # Ctrl+W for word study
        self.bind("<Control-comma>", lambda e: self.apply_dark_mode())  # Ctrl+, for dark mode
        self.bind("<Control-period>", lambda e: self.apply_light_mode())  # Ctrl+. for light mode
        self.bind("<F5>", lambda e: self.render_all())  # F5 to refresh
        self.bind("<F1>", lambda e: self.open_help_window())  # F1 for help
        self.bind("<Alt-Left>", lambda e: self.go_back())  # Alt+Left for back
        self.bind("<Alt-Right>", lambda e: self.go_forward())  # Alt+Right for forward

    def available_books(self):
        books = BIBLE.get(self.translation, {})
        if self.translation == "KJV":
            extras = sorted(book for book in books if book not in BOOK_ORDER)
            return BOOK_ORDER + extras
        if self.translation == "JPS1917":
            extras = sorted(book for book in books if book not in TANAKH_BOOKS)
            return TANAKH_BOOKS + extras
        ordered = [book for book in BOOK_ORDER if book in books]
        extras = sorted(book for book in books if book not in ordered)
        return ordered + extras

    def chapter_count(self, book=None):
        book = book or self.current_book
        if self.translation in ("KJV", "JPS1917") and book in BOOK_CHAPTERS:
            return BOOK_CHAPTERS[book]
        chapters = BIBLE.get(self.translation, {}).get(book, {})
        return max(chapters) if chapters else 0

    def chapter_is_available(self, book, chapter):
        return bool(BIBLE.get(self.translation, {}).get(book, {}).get(chapter))

    def available_chapters(self, book=None):
        book = book or self.current_book
        chapters = BIBLE.get(self.translation, {}).get(book, {})
        return sorted(chapter for chapter, verses in chapters.items() if verses)

    def first_available_reference(self, book=None):
        requested_book = book
        book = book or (self.available_books()[0] if self.available_books() else "")
        chapters = self.available_chapters(book)
        if requested_book and not chapters:
            return book, 1, 1
        if not book:
            return "Genesis", 1, 1
        if not chapters:
            return book, 1, 1
        return book, chapters[0], 1

    def translation_choices(self):
        choices = []
        labels = dict(TRANSLATION_LABELS)
        labels.update(BUNDLED_TRANSLATION_LABELS)
        for code in sorted(labels, key=lambda item: (item not in ("KJV", "JPS1917"), item)):
            label = labels[code]
            if code in BIBLE:
                status = "local"
            elif code == "JPS1917":
                status = "online/cache"
            else:
                status = "import needed"
            choices.append(f"{code} - {label} ({status})")
        return choices

    def translation_choice_for(self, code):
        for choice in self.translation_choices():
            if choice.startswith(f"{code} - "):
                return choice
        return code

    def translation_code_from_choice(self, choice):
        return str(choice).split(" - ", 1)[0].strip()

    def check_connection_async(self):
        self.background.submit(self.check_connection_worker, on_success=self.set_connection_status, on_error=lambda _exc: self.set_connection_status(False))

    def check_connection_worker(self):
        try:
            fetch_url("https://bible-api.com/John%201:1?translation=kjv", timeout=CONNECTION_CHECK_TIMEOUT, max_retries=1)
            return True
        except Exception as exc:
            logger.info("Connection check failed; app will use local library. Error: %s", exc)
            return False

    def set_connection_status(self, online):
        if online:
            self.connection_var.set("Online - web access available")
            self.connection_button.configure(bg="#2f7d4f", fg="white")
        else:
            self.connection_var.set("Offline - using local library")
            self.connection_button.configure(bg="#b64b3f", fg="white")

    def request_chapter_fetch(self, book, chapter, verse=1, target_ref=None):
        if self.translation not in ("KJV", "JPS1917"):
            messagebox.showinfo(
                "Chapter Not Available",
                "Only KJV and JPS 1917 chapters can be fetched online automatically. Use Import JSON for this translation.",
            )
            return
        if book not in BOOK_CHAPTERS or chapter < 1 or chapter > BOOK_CHAPTERS[book]:
            messagebox.showinfo("Passage Lookup", "That chapter is not valid for this translation.")
            return
        if self.translation == "JPS1917" and book not in JPS_BOOK_CODES:
            messagebox.showinfo("Passage Lookup", "That book is not part of the JPS 1917 Hebrew Bible / Tanakh.")
            return
        key = (self.translation, book, chapter)
        if key in self.fetching_chapters:
            return

        translation = self.translation
        self.current_book = book
        self.current_chapter = chapter
        self.selected_ref = target_ref or f"{book} {chapter}:{verse}"
        self.fetching_chapters.add(key)
        self.library_status.set(f"Fetching {translation} {book} {chapter}...")
        if hasattr(self, "chapter_list"):
            self.chapter_list.configure(state="disabled")
        self.render_all()
        self.background.submit(
            lambda: self.fetch_chapter_worker(translation, book, chapter, verse, target_ref),
            on_success=lambda result: self.cache_fetched_chapter(*result),
            on_error=lambda error: self.chapter_fetch_failed(translation, book, chapter, error),
        )

    def fetch_chapter_worker(self, translation, book, chapter, verse, target_ref):
        logger.info("Fetching chapter: %s %s %s", translation, book, chapter)
        verses = fetch_translation_chapter(translation, book, chapter)
        return translation, book, chapter, verse, verses, target_ref

    def cache_fetched_chapter(self, translation, book, chapter, verse, verses, target_ref=None):
        BIBLE.setdefault(translation, {}).setdefault(book, {})[chapter] = verses
        save_bible_library("Local Bible cache")
        self.lookup_cache.clear(translation)
        logger.info("Cached fetched chapter: %s %s %s (%s verses)", translation, book, chapter, len(verses))
        self.fetching_chapters.discard((translation, book, chapter))
        self.library_label = "Local Bible cache"
        self.library_status.set(f"Saved {translation} {book} {chapter} for offline reading.")
        if hasattr(self, "chapter_list"):
            self.chapter_list.configure(state="normal")
        if hasattr(self, "translation_combo"):
            self.translation_combo.configure(values=self.translation_choices())
            self.translation_var.set(self.translation_choice_for(self.translation))
        self.open_reference(target_ref or f"{book} {chapter}:{verse}")

    def chapter_fetch_failed(self, translation, book, chapter, error):
        self.fetching_chapters.discard((translation, book, chapter))
        self.library_status.set(f"Could not fetch {translation} {book} {chapter}.")
        if hasattr(self, "chapter_list"):
            self.chapter_list.configure(state="normal")
        self.render_chapter()
        messagebox.showerror(
            "Online Chapter Fetch",
            f"Could not fetch {translation} {book} {chapter}.\n\nCheck your internet connection and try again.\n\n{error}",
        )

    def download_full_kjv(self):
        if self.download_busy:
            return
        if not messagebox.askyesno(
            "Install Full KJV",
            "Install the bundled full KJV text into the local library?\n\nThis uses the local file included with the app, so it should finish quickly and will work offline.",
        ):
            return
        self.download_busy = True
        self.library_status.set("Installing full KJV from the local bundle...")
        self.background.submit(self.download_full_kjv_worker, on_success=self.full_kjv_finished, on_error=self.full_kjv_failed)

    def download_full_kjv_worker(self):
        logger.info("Installing bundled full KJV")
        translation, label = bundled_translation_for("KJV")
        if not translation:
            raise RuntimeError("The bundled KJV file could not be found or loaded.")
        BIBLE["KJV"] = translation
        save_bible_library("KJV full local")
        logger.info("Bundled full KJV installed")
        return label or "KJV full local"

    def full_kjv_failed(self, error):
        logger.error("Bundled full KJV install failed: %s", error)
        self.download_busy = False
        messagebox.showerror("Install Full KJV", f"Install failed:\n{error}")
        self.library_status.set("Install failed. Existing local library is unchanged.")

    def full_kjv_finished(self, label):
        self.download_busy = False
        self.lookup_cache.clear()
        self.load_downloaded_library(label)

    def start_chapter_batch_download(self, books, label, translation=None):
        if self.download_busy:
            messagebox.showinfo("Library Manager", "A download is already running.")
            return
        translation = translation or self.translation
        if translation not in ("KJV", "JPS1917"):
            messagebox.showinfo("Library Manager", "Only KJV and JPS 1917 can be downloaded automatically.")
            return
        self.download_busy = True
        self.library_status.set(f"Starting {translation} {label} download...")
        self.background.submit(
            lambda: self.chapter_batch_download_worker(translation, books, label),
            on_success=self.finish_batch_download,
            on_error=lambda error: self.batch_download_failed(label, error),
        )

    def chapter_batch_download_worker(self, translation, books, label):
        try:
            logger.info("Starting batch chapter download: %s %s", translation, label)
            total = sum(BOOK_CHAPTERS.get(book, 0) for book in books)
            done = 0
            for book in books:
                if translation == "JPS1917" and book not in JPS_BOOK_CODES:
                    continue
                BIBLE.setdefault(translation, {}).setdefault(book, {})
                for chapter in range(1, BOOK_CHAPTERS.get(book, 0) + 1):
                    if not BIBLE[translation][book].get(chapter):
                        BIBLE[translation][book][chapter] = fetch_translation_chapter(translation, book, chapter)
                    done += 1
                    self.after(0, lambda d=done, t=total, b=book, c=chapter, tr=translation: self.library_status.set(f"Downloading {tr} {label}: {d}/{t} ({b} {c})"))
            save_bible_library("Local Bible cache")
            logger.info("Finished batch chapter download: %s %s", translation, label)
            return f"{translation} {label}"
        finally:
            self.download_busy = False

    def batch_download_failed(self, label, error):
        logger.error("Batch chapter download failed: %s: %s", label, error)
        messagebox.showerror("Library Manager", f"Download failed:\n{error}")
        self.library_status.set(f"{label} download failed.")

    def finish_batch_download(self, label):
        self.lookup_cache.clear()
        self.library_label = "KJV local cache"
        self.library_status.set(f"Saved {label} for offline reading.")
        self.render_all()
        messagebox.showinfo("Library Manager", f"{label} has been saved for offline reading.")

    def clear_kjv_cache(self):
        if not messagebox.askyesno("Clear KJV Cache", "Clear downloaded/imported KJV chapters and return to the starter sample?\n\nYour notes, journal, and bookmarks will not be deleted."):
            return
        global BIBLE
        sample = normalize_bible_data(sample_bible())
        BIBLE["KJV"] = sample["KJV"]
        self.library_label = "KJV sample"
        if BIBLE_DATA_PATH.exists():
            backup_file(BIBLE_DATA_PATH)
            if set(BIBLE.keys()) == {"KJV"}:
                BIBLE_DATA_PATH.unlink()
            else:
                save_bible_library("Local Bible cache")
        self.translation = "KJV"
        self.current_book, self.current_chapter, first_verse = self.first_available_reference()
        self.selected_ref = f"{self.current_book} {self.current_chapter}:{first_verse}"
        self.library_status.set("KJV cache cleared. Loaded starter sample.")
        self.render_all()
        self.select_verse(self.selected_ref)

    def cached_chapter_count(self, book=None, translation=None):
        translation = translation or self.translation
        if book:
            return len([chapter for chapter, verses in BIBLE.get(translation, {}).get(book, {}).items() if verses])
        return sum(len([chapter for chapter, verses in chapters.items() if verses]) for chapters in BIBLE.get(translation, {}).values())

    def open_library_window(self):
        LibraryWindow(self)

    def load_downloaded_library(self, label):
        global BIBLE
        BIBLE, self.library_label = load_bible_library()
        self.lookup_cache.clear()
        if hasattr(self, "translation_combo"):
            self.translation_combo.configure(values=self.translation_choices())
        if self.translation not in BIBLE:
            self.translation = "KJV" if "KJV" in BIBLE else next(iter(BIBLE), self.translation)
        self.translation_var.set(self.translation_choice_for(self.translation))
        self.library_status.set(f"Loaded: {label}")
        self.current_book, self.current_chapter, first_verse = self.first_available_reference()
        self.selected_ref = f"{self.current_book} {self.current_chapter}:{first_verse}"
        self.render_all()
        self.select_verse(self.selected_ref)
        messagebox.showinfo("Install Full KJV", "The full KJV local library has been saved.")

    def import_bible_json(self):
        path = filedialog.askopenfilename(
            title="Import Bible JSON",
            initialdir=str(APP_DIR),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("translations"):
                translations = normalize_bible_data(data["translations"])
                label = data.get("label", "Imported Bible")
            else:
                translations = normalize_bible_data(data)
                label = "Imported Bible"
            supported = set(TRANSLATION_LABELS)
            if not supported.intersection(translations):
                raise RuntimeError("The JSON needs at least one supported translation key: KJV, NIV, or ESV.")
            existing = {}
            if BIBLE_DATA_PATH.exists():
                try:
                    existing_payload = json.loads(BIBLE_DATA_PATH.read_text(encoding="utf-8"))
                    existing = normalize_bible_data(existing_payload.get("translations", existing_payload))
                except Exception as exc:
                    logger.warning("Could not read existing Bible JSON during import; replacing supported translations. Error: %s", exc)
                    existing = {}
            existing.update({code: data for code, data in translations.items() if code in supported})
            write_json(BIBLE_DATA_PATH, {"label": label, "translations": existing})
            self.load_downloaded_library(label)
        except Exception as exc:
            messagebox.showerror("Import Bible JSON", f"Could not import that file:\n{exc}")

    def open_document_converter(self):
        DocumentConversionWindow(self)

    def open_web_commentary_importer(self):
        WebCommentaryImportWindow(self)

    def open_hymnal_window(self):
        HymnalViewerWindow(self)

    def open_study_dashboard(self):
        StudyDashboardWindow(self)

    def open_study_worksheet(self):
        PassageStudyWorksheetWindow(self, self.selected_ref)

    def open_search_everything(self):
        SearchEverythingWindow(self, PEOPLE, MAPS, MapViewerWindow, DocumentViewerWindow)

    def open_timeline_window(self):
        TimelineWindow(self, MAPS)

    def open_study_binder(self):
        StudyBinderWindow(self, maps_for_reference)

    def open_presentation_mode(self):
        PresentationWindow(self)

    def open_cross_reference_explorer(self):
        CrossReferenceExplorerWindow(self, self.selected_ref)

    def remember_recent_reference(self, ref):
        normalized = normalized_reference(ref) if ":" in str(ref) else str(ref).strip()
        if not normalized:
            return
        self.recent_references = [
            item for item in self.recent_references
            if item.get("reference") != normalized
        ]
        self.recent_references.insert(0, {
            "reference": normalized,
            "opened": datetime.now().isoformat(timespec="seconds"),
        })
        self.recent_references = self.recent_references[:30]
        write_recent_references(self.recent_references)

    def hymn_key(self, item):
        return (item.get("hymnal", ""), str(item.get("number", "")), item.get("title", ""))

    def remember_recent_hymn(self, hymn, hymnal_name):
        item = {
            "title": hymn.get("title", ""),
            "hymnal": hymnal_name,
            "number": str(hymn.get("number", "")),
            "page": int(hymn.get("page", 0) or 0),
            "added": datetime.now().isoformat(timespec="seconds"),
        }
        self.recent_hymns = [existing for existing in self.recent_hymns if self.hymn_key(existing) != self.hymn_key(item)]
        self.recent_hymns.insert(0, item)
        write_recent_hymns(self.recent_hymns)

    def toggle_hymn_favorite(self, hymn, hymnal_name):
        item = {
            "title": hymn.get("title", ""),
            "hymnal": hymnal_name,
            "number": str(hymn.get("number", "")),
            "page": int(hymn.get("page", 0) or 0),
            "added": datetime.now().isoformat(timespec="seconds"),
        }
        key = self.hymn_key(item)
        if any(self.hymn_key(existing) == key for existing in self.hymn_favorites):
            self.hymn_favorites = [existing for existing in self.hymn_favorites if self.hymn_key(existing) != key]
            action = "Removed from hymn favorites."
        else:
            self.hymn_favorites.insert(0, item)
            action = "Added to hymn favorites."
        write_hymn_favorites(self.hymn_favorites)
        return action

    def link_hymn_to_reference(self, ref, hymn, hymnal_name):
        normalized = normalized_reference(ref)
        if not normalized:
            return "Select a Bible passage first."
        item = {
            "title": hymn.get("title", ""),
            "hymnal": hymnal_name,
            "number": str(hymn.get("number", "")),
            "page": int(hymn.get("page", 0) or 0),
            "linked": datetime.now().isoformat(timespec="seconds"),
        }
        links = self.hymn_links.setdefault(normalized, [])
        key = self.hymn_key(item)
        if not any(self.hymn_key(existing) == key for existing in links):
            links.append(item)
            write_hymn_links(self.hymn_links)
        return f"Linked hymn to {normalized}."

    def add_user_cross_reference(self, source, target, reason):
        source_ref = normalized_reference(source)
        target_ref = normalized_reference(target)
        if not source_ref or not target_ref:
            return False
        items = self.user_cross_references.setdefault(source_ref, [])
        if not any(item.get("target") == target_ref for item in items):
            items.append({"target": target_ref, "reason": reason.strip() or "User link"})
            write_user_cross_references(self.user_cross_references)
        return True

    def grouped_cross_references(self, ref):
        entry = STUDY.get(ref, {})
        groups = {
            "Curated": [{"target": cross_ref, "reason": "Study note cross-reference"} for cross_ref in entry.get("cross", [])],
            "Themes": [{"target": theme_ref, "reason": theme} for theme in themes_for_reference(ref) for theme_ref in THEMES.get(theme, []) if theme_ref != ref],
            "People": [],
            "Places / Maps": [],
            "Language": [],
            "User Links": list(self.user_cross_references.get(ref, [])),
        }
        for person in entry.get("people", []):
            for person_ref in PEOPLE.get(person, {}).get("references", [])[:8]:
                if person_ref != ref:
                    groups["People"].append({"target": person_ref, "reason": person})
        for map_item in maps_for_reference(ref)[:6]:
            for map_ref in map_item.get("related_passages", [])[:5]:
                if map_ref != ref:
                    groups["Places / Maps"].append({"target": map_ref, "reason": map_item.get("title", "Map")})
        for word, original, _note in entry.get("language", []):
            for other_ref, other_entry in STUDY.items():
                if other_ref == ref:
                    continue
                for other_word, other_original, _other_note in other_entry.get("language", []):
                    if original and other_original == original:
                        groups["Language"].append({"target": other_ref, "reason": f"{word} / {original}"})
        deduped = {}
        for group, items in groups.items():
            seen = set()
            cleaned = []
            for item in items:
                target = normalized_reference(item.get("target", ""))
                if not target or target in seen:
                    continue
                seen.add(target)
                cleaned.append({"target": target, "reason": item.get("reason", "")})
            deduped[group] = cleaned
        return deduped

    def document_conversion_finished(self, item):
        self.library_documents = read_document_library()
        self.library_status.set(f"Converted document: {item.get('title', '')}")
        messagebox.showinfo("Document Converted", f"Added to Library Manager:\n{item.get('title', '')}")

    def open_niv_pdf(self):
        if not NIV_PDF_PATH.exists():
            messagebox.showinfo("NIV PDF", "The local NIV-Bible.pdf file was not found in the data folder.")
            return
        try:
            os.startfile(str(NIV_PDF_PATH))
        except Exception as exc:
            logger.exception("Could not open NIV PDF: %s", NIV_PDF_PATH)
            messagebox.showerror("Open NIV PDF", f"Could not open NIV-Bible.pdf:\n{exc}")

    def ensure_niv_pdf_in_background(self):
        if not NIV_PDF_PATH.exists():
            return
        if matching_document_for_source(self.library_documents, NIV_PDF_PATH):
            return
        if self.niv_pdf_import_busy:
            return
        self.niv_pdf_import_busy = True
        self.library_status.set("Adding NIV PDF to searchable Library Manager documents...")
        self.background.submit(self.ensure_niv_pdf_worker, on_success=lambda result: self.finish_niv_pdf_document(*result), on_error=self.niv_pdf_failed)

    def add_niv_pdf_to_library(self):
        if not NIV_PDF_PATH.exists():
            messagebox.showinfo("NIV PDF", "The local NIV-Bible.pdf file was not found in the data folder.")
            return
        if self.niv_pdf_import_busy:
            messagebox.showinfo("NIV PDF", "The NIV PDF is already being added to the searchable documents.")
            return
        self.niv_pdf_import_busy = True
        self.library_status.set("Adding NIV PDF to searchable Library Manager documents...")
        self.background.submit(self.ensure_niv_pdf_worker, on_success=lambda result: self.finish_niv_pdf_document(*result), on_error=self.niv_pdf_failed)

    def ensure_niv_pdf_worker(self):
        return ensure_niv_pdf_document(
            progress=lambda value, message: self.after(0, lambda m=message: self.library_status.set(f"NIV PDF: {m}"))
        )

    def niv_pdf_failed(self, error):
        logger.error("Could not add NIV PDF to searchable document library: %s", error)
        self.library_status.set(f"Could not add NIV PDF to documents: {error}")
        self.niv_pdf_import_busy = False

    def finish_niv_pdf_document(self, item, created):
        self.library_documents = read_document_library()
        self.niv_pdf_import_busy = False
        if created:
            self.library_status.set("NIV PDF added to searchable Library Manager documents.")
        else:
            self.library_status.set("NIV PDF is already in Library Manager documents.")

    def build_left(self, parent):
        # Create a frame to hold canvas and scrollbar
        left_frame = tk.Frame(parent, bg=APP_PANEL)
        left_frame.pack(fill="both", expand=True)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(left_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Create canvas for scrolling
        canvas = tk.Canvas(left_frame, yscrollcommand=scrollbar.set, relief="flat", highlightthickness=0, bg=APP_PANEL)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold all content
        content_frame = tk.Frame(canvas, bg=APP_PANEL)
        content_window = canvas.create_window(0, 0, window=content_frame, anchor="nw")
        canvas.bind("<Configure>", lambda event, c=canvas, w=content_window: c.itemconfigure(w, width=event.width))
        content_frame.bind("<Configure>", lambda _event, c=canvas: c.configure(scrollregion=c.bbox("all")))
        
        # Bind mouse wheel to canvas
        canvas.bind("<MouseWheel>", lambda e: self._on_canvas_mousewheel(e, canvas))
        canvas.bind("<Button-4>", lambda e: self._on_canvas_mousewheel(e, canvas))
        canvas.bind("<Button-5>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<MouseWheel>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<Button-4>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<Button-5>", lambda e: self._on_canvas_mousewheel(e, canvas))
        
        # Pack all widgets into content_frame
        ttk.Label(content_frame, text="Local Library", style="Section.TLabel").pack(anchor="w", padx=5)
        self.connection_var = tk.StringVar(value="Checking web...")
        self.connection_button = tk.Button(content_frame, textvariable=self.connection_var, bg="#b64b3f", fg="white", relief="flat")
        self.connection_button.pack(fill="x", pady=(4, 6), padx=5)
        actions = tk.Frame(content_frame, bg=APP_PANEL)
        actions.pack(fill="x", pady=(0, 8), padx=5)
        action_items = [
            ("Full KJV", self.download_full_kjv),
            ("Import", self.import_bible_json),
            ("NIV PDF", self.open_niv_pdf),
            ("NIV Search", self.add_niv_pdf_to_library),
            ("Convert Doc", self.open_document_converter),
            ("Library", self.open_library_window),
            ("Hymnals", self.open_hymnal_window),
        ]
        for index, (label, command) in enumerate(action_items):
            row = index // 2
            col = index % 2
            button = RoundedButton(actions, label, command)
            button.grid(row=row, column=col, sticky="ew", padx=(0, 6 if col == 0 else 0), pady=(0, 6))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)
        self.library_status = self.app_status_var
        self.library_status.set(f"Loaded: {self.library_label}")
        ttk.Label(content_frame, textvariable=self.library_status, style="Muted.TLabel", wraplength=260).pack(anchor="w", pady=(0, 10), padx=5)

        ttk.Label(content_frame, text="Translation", style="Section.TLabel").pack(anchor="w", padx=5)
        self.translation_var = tk.StringVar(value=self.translation_choice_for(self.translation))
        self.translation_combo = ttk.Combobox(content_frame, textvariable=self.translation_var, values=self.translation_choices(), state="readonly")
        self.translation_combo.pack(fill="x", pady=(4, 10), padx=5)
        self.translation_combo.bind("<<ComboboxSelected>>", self.on_translation_selected)

        ttk.Label(content_frame, text="Books", style="Section.TLabel").pack(anchor="w", padx=5)
        self.book_list = tk.Listbox(content_frame, height=8, exportselection=False)
        self.book_list.pack(fill="x", pady=(4, 10), padx=5)
        self.book_list.bind("<<ListboxSelect>>", self.on_book_selected)

        ttk.Label(content_frame, text="Chapters", style="Section.TLabel").pack(anchor="w", padx=5)
        self.chapter_list = tk.Listbox(content_frame, height=5, exportselection=False)
        self.chapter_list.pack(fill="x", pady=(4, 10), padx=5)
        self.chapter_list.bind("<<ListboxSelect>>", self.on_chapter_selected)

        ttk.Label(content_frame, text="Concordance Search", style="Section.TLabel").pack(anchor="w", padx=5)
        ttk.Label(content_frame, text="Search scans cached local chapters only.", style="Muted.TLabel", wraplength=260).pack(anchor="w", padx=5)
        search_row = ttk.Frame(content_frame)
        search_row.pack(fill="x", pady=(4, 6), padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        search_entry.bind("<Return>", lambda _event: self.search_word())
        ttk.Button(search_row, text="Find", command=self.search_word).pack(side="left")
        search_options = ttk.Frame(content_frame)
        search_options.pack(fill="x", pady=(0, 6), padx=5)
        self.search_exact_var = tk.BooleanVar(value=False)
        self.search_whole_word_var = tk.BooleanVar(value=False)
        self.search_context_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(search_options, text="Exact phrase", variable=self.search_exact_var).pack(anchor="w")
        ttk.Checkbutton(search_options, text="Whole word", variable=self.search_whole_word_var).pack(anchor="w")
        ttk.Checkbutton(search_options, text="Context", variable=self.search_context_var).pack(anchor="w")
        search_scope_row = ttk.Frame(content_frame)
        search_scope_row.pack(fill="x", pady=(0, 6), padx=5)
        self.search_range_var = tk.StringVar(value="Whole Bible")
        self.search_sort_var = tk.StringVar(value="Book order")
        ttk.Combobox(search_scope_row, textvariable=self.search_range_var, values=list(SEARCH_RANGES), state="readonly", width=15).pack(side="left", fill="x", expand=True)
        ttk.Combobox(search_scope_row, textvariable=self.search_sort_var, values=["Book order", "Relevance"], state="readonly", width=12).pack(side="left", padx=(6, 0))
        self.result_list = tk.Listbox(content_frame, height=9, exportselection=False)
        self.result_list.pack(fill="both", expand=True, pady=(0, 10), padx=5)
        self.result_list.bind("<<ListboxSelect>>", self.on_result_selected)

        ttk.Label(content_frame, text="Thematic Tracing", style="Section.TLabel").pack(anchor="w", padx=5)
        self.theme_list = tk.Listbox(content_frame, height=7, exportselection=False)
        self.theme_list.pack(fill="x", pady=(4, 0), padx=5)
        self.theme_list.bind("<<ListboxSelect>>", self.on_theme_selected)
        ttk.Button(content_frame, text="Concept Study Library", command=self.open_concept_library).pack(fill="x", pady=(6, 0), padx=5)

        ttk.Label(content_frame, text="People", style="Section.TLabel").pack(anchor="w", pady=(10, 0), padx=5)
        people_row = ttk.Frame(content_frame)
        people_row.pack(fill="x", pady=(4, 6), padx=5)
        self.people_search_var = tk.StringVar()
        people_entry = ttk.Entry(people_row, textvariable=self.people_search_var)
        people_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        people_entry.bind("<Return>", lambda _event: self.render_people())
        people_entry.bind("<KeyRelease>", lambda _event: self.render_people())
        ttk.Button(people_row, text="Find", command=self.render_people).pack(side="left")
        self.people_list = tk.Listbox(content_frame, height=7, exportselection=False)
        self.people_list.pack(fill="x", pady=(0, 0), padx=5)
        self.people_list.bind("<<ListboxSelect>>", self.on_person_selected)
        ttk.Button(content_frame, text="People Reference", command=self.open_people_reference_window).pack(fill="x", pady=(6, 0), padx=5)

        ttk.Label(content_frame, text="Bookmarks", style="Section.TLabel").pack(anchor="w", pady=(10, 0), padx=5)
        bookmark_buttons = ttk.Frame(content_frame)
        bookmark_buttons.pack(fill="x", pady=(4, 6), padx=5)
        ttk.Button(bookmark_buttons, text="Add", command=self.add_bookmark).pack(side="left", fill="x", expand=True)
        ttk.Button(bookmark_buttons, text="Remove", command=self.remove_selected_bookmark).pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.bookmark_list = tk.Listbox(content_frame, height=6, exportselection=False)
        self.bookmark_list.pack(fill="x", pady=(0, 0), padx=5)
        self.bookmark_list.bind("<<ListboxSelect>>", self.on_bookmark_selected)
        
        # Update scroll region after all widgets are packed
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def build_center(self, parent):
        title_row = ttk.Frame(parent)
        title_row.pack(fill="x")
        self.chapter_title = ttk.Label(title_row, text="", style="Title.TLabel")
        self.chapter_title.pack(side="left", anchor="w")
        
        # Create a frame to hold the text widget and scrollbar
        text_frame = tk.Frame(parent, bg=APP_PANEL)
        text_frame.pack(fill="both", expand=True, pady=(10, 0))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollbar for the reader text widget
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.reader = tk.Text(text_frame, wrap="word", padx=14, pady=12, relief="flat", yscrollcommand=scrollbar.set)
        self.reader.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.reader.yview)
        
        self.reader.tag_configure("verse_number", foreground="#b8872f", font=("Segoe UI", 8, "bold"))
        
        # Bind highlighting keyboard shortcuts
        self.reader.bind("<Control-h>", self.apply_highlight)  # Ctrl+H to highlight
        self.reader.bind("<Control-u>", self.remove_highlight)  # Ctrl+U to un-highlight
        
        # Bind mouse wheel scrolling - BEFORE setting state to disabled
        self.reader.bind("<MouseWheel>", self.on_mousewheel)
        self.reader.bind("<Button-4>", self.on_mousewheel)  # Linux scroll up
        self.reader.bind("<Button-5>", self.on_mousewheel)  # Linux scroll down
        
        # Bind right-click context menu
        self.reader.bind("<Button-3>", self.show_reader_context_menu)  # Right-click menu
        
        self.apply_reader_settings()
        
        # IMPORTANT: Keep text widget NORMAL to allow scrolling
        # This will prevent editing through other means below
        self.reader.bind("<Key>", lambda e: "break")  # Block all keyboard input
        self.reader.bind("<Control-v>", lambda e: "break")  # Block paste
        self.reader.bind("<Button-2>", lambda e: "break")  # Block middle mouse paste

    def build_right(self, parent):
        # Create a frame to hold canvas and scrollbar
        right_frame = tk.Frame(parent, bg=APP_PANEL)
        right_frame.pack(fill="both", expand=True)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(right_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Create canvas for scrolling
        canvas = tk.Canvas(right_frame, yscrollcommand=scrollbar.set, relief="flat", highlightthickness=0, bg=APP_PANEL)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=canvas.yview)
        
        # Create frame inside canvas to hold all content
        content_frame = tk.Frame(canvas, bg=APP_PANEL)
        content_window = canvas.create_window(0, 0, window=content_frame, anchor="nw")
        canvas.bind("<Configure>", lambda event, c=canvas, w=content_window: c.itemconfigure(w, width=event.width))
        content_frame.bind("<Configure>", lambda _event, c=canvas: c.configure(scrollregion=c.bbox("all")))
        
        # Bind mouse wheel to canvas
        canvas.bind("<MouseWheel>", lambda e: self._on_canvas_mousewheel(e, canvas))
        canvas.bind("<Button-4>", lambda e: self._on_canvas_mousewheel(e, canvas))
        canvas.bind("<Button-5>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<MouseWheel>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<Button-4>", lambda e: self._on_canvas_mousewheel(e, canvas))
        content_frame.bind("<Button-5>", lambda e: self._on_canvas_mousewheel(e, canvas))
        
        # Pack all widgets into content_frame
        ttk.Label(content_frame, text="Selected Verse", style="Section.TLabel").pack(anchor="w")
        self.selected_label = ttk.Label(content_frame, text="", font=("Segoe UI", 11, "bold"))
        self.selected_label.pack(anchor="w", pady=(4, 2), padx=5)
        self.selected_text = tk.Text(content_frame, height=5, width=34, wrap="word", relief="solid", borderwidth=1)
        self.selected_text.pack(fill="x", pady=(0, 12), padx=5)
        self.selected_text.configure(state="disabled")

        ttk.Label(content_frame, text="Teaching Notes", style="Section.TLabel").pack(anchor="w", padx=5)
        self.teaching_text = tk.Text(content_frame, height=5, width=34, wrap="word", relief="solid", borderwidth=1)
        self.teaching_text.pack(fill="x", pady=(4, 12), padx=5)
        self.teaching_text.configure(state="disabled")

        ttk.Label(content_frame, text="Cross References", style="Section.TLabel").pack(anchor="w", padx=5)
        self.cross_list = tk.Listbox(content_frame, height=5, width=34, exportselection=False)
        self.cross_list.pack(fill="x", pady=(4, 12), padx=5)
        self.cross_list.bind("<<ListboxSelect>>", self.on_cross_selected)
        cross_buttons = ttk.Frame(content_frame)
        cross_buttons.pack(fill="x", pady=(0, 12), padx=5)
        ttk.Button(cross_buttons, text="Explorer", command=self.open_cross_reference_explorer).pack(side="left", fill="x", expand=True)
        ttk.Button(cross_buttons, text="Graph", command=self.open_cross_reference_graph).pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(content_frame, text="Themes / Word Hits", style="Section.TLabel").pack(anchor="w", padx=5)
        self.dashboard_text = tk.Text(content_frame, height=6, width=34, wrap="word", relief="solid", borderwidth=1)
        self.dashboard_text.pack(fill="x", pady=(4, 12), padx=5)
        self.dashboard_text.configure(state="disabled")

        ttk.Label(content_frame, text="Original Language", style="Section.TLabel").pack(anchor="w", padx=5)
        self.language_text = tk.Text(content_frame, height=5, width=34, wrap="word", relief="solid", borderwidth=1)
        self.language_text.pack(fill="x", pady=(4, 12), padx=5)
        self.language_text.configure(state="disabled")

        ttk.Label(content_frame, text="Map / Place Reference", style="Section.TLabel").pack(anchor="w", padx=5)
        self.map_text = tk.Text(content_frame, height=4, width=34, wrap="word", relief="solid", borderwidth=1)
        self.map_text.pack(fill="x", pady=(4, 8), padx=5)
        self.map_text.configure(state="disabled")
        self.map_list = tk.Listbox(content_frame, height=4, width=34, exportselection=False)
        self.map_list.pack(fill="x", pady=(0, 6), padx=5)
        self.map_list.bind("<<ListboxSelect>>", self.on_map_selected)
        ttk.Button(content_frame, text="Open Selected Map", command=self.open_selected_map).pack(fill="x", pady=(0, 12), padx=5)

        ttk.Label(content_frame, text="People In This Passage", style="Section.TLabel").pack(anchor="w", padx=5)
        self.passage_people_list = tk.Listbox(content_frame, height=4, width=34, exportselection=False)
        self.passage_people_list.pack(fill="x", pady=(4, 12), padx=5)
        self.passage_people_list.bind("<<ListboxSelect>>", self.on_passage_person_selected)

        ttk.Label(content_frame, text="Related Hymns", style="Section.TLabel").pack(anchor="w", padx=5)
        self.related_hymn_list = tk.Listbox(content_frame, height=4, width=34, exportselection=False)
        self.related_hymn_list.pack(fill="x", pady=(4, 6), padx=5)
        ttk.Button(content_frame, text="Open Hymnal Reader", command=self.open_hymnal_window).pack(fill="x", pady=(0, 12), padx=5)

        ttk.Label(content_frame, text="Local Commentary", style="Section.TLabel").pack(anchor="w", padx=5)
        self.commentary_text = tk.Text(content_frame, height=7, width=34, wrap="word", relief="solid", borderwidth=1)
        self.commentary_text.pack(fill="x", pady=(4, 8), padx=5)
        self.commentary_text.configure(state="disabled")
        ttk.Button(content_frame, text="Import Commentary Markdown", command=self.import_commentary_file).pack(fill="x", pady=(0, 12), padx=5)
        ttk.Button(content_frame, text="Save Web Commentary", command=self.open_web_commentary_importer).pack(fill="x", pady=(0, 12), padx=5)

        ttk.Label(content_frame, text="Personal Notes", style="Section.TLabel").pack(anchor="w", padx=5)
        self.note_status_var = tk.StringVar(value="")
        ttk.Label(content_frame, textvariable=self.note_status_var, style="Muted.TLabel").pack(anchor="w", padx=5)
        self.note_text = tk.Text(content_frame, height=7, width=34, wrap="word", undo=True, maxundo=100, autoseparators=True)
        self.note_text.pack(fill="both", expand=True, pady=(4, 8), padx=5)
        self.note_text.bind("<KeyRelease>", self.on_note_changed)
        self.note_text.bind("<Control-z>", lambda _event: self.undo_note())
        self.note_text.bind("<Control-y>", lambda _event: self.redo_note())
        note_buttons = ttk.Frame(content_frame)
        note_buttons.pack(fill="x", padx=5)
        ttk.Button(note_buttons, text="Save Note", command=self.save_note).pack(side="left", fill="x", expand=True)
        ttk.Button(note_buttons, text="Clear", command=self.clear_note).pack(side="left", fill="x", expand=True, padx=(8, 0))
        note_edit_buttons = ttk.Frame(content_frame)
        note_edit_buttons.pack(fill="x", padx=5, pady=(6, 0))
        ttk.Button(note_edit_buttons, text="Undo", command=self.undo_note).pack(side="left", fill="x", expand=True)
        ttk.Button(note_edit_buttons, text="Redo", command=self.redo_note).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(content_frame, text="Study Worksheet", command=self.open_study_worksheet).pack(fill="x", pady=(10, 0), padx=5)
        ttk.Button(content_frame, text="Add to Study Session", command=self.add_current_ref_to_session).pack(fill="x", pady=(10, 0), padx=5)
        ttk.Button(content_frame, text="Export Notes / Journal", command=self.export_notes_journal).pack(fill="x", pady=(10, 0), padx=5)
        ttk.Button(content_frame, text="Journal This", command=self.open_journal_window, style="Primary.TButton").pack(fill="x", pady=(10, 0), padx=5)
        
        # Update scroll region after all widgets are packed
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def apply_reader_settings(self):
        if not hasattr(self, "reader"):
            return
        bg = self.settings.get("reader_bg", "#fbfcfd")
        fg = self.settings.get("reader_fg", "#1F1F1F")
        highlight = self.settings.get("highlight_bg", "#edf6f5")
        font_name = self.settings.get("reader_font", "Georgia")
        font_size = int(self.settings.get("reader_font_size", 13))
        self.configure(bg=APP_BG)
        
        style = ttk.Style(self)
        style.configure("Reader.TFrame", background=APP_PANEL)
        style.configure("Reader.TPanedwindow", background=APP_BG)
        style.configure("Title.TLabel", background=APP_PANEL, foreground="#1F1F1F")
        style.configure("Section.TLabel", background=APP_PANEL, foreground="#1F1F1F")
        style.configure("Muted.TLabel", background=APP_PANEL, foreground="#616161")
        style.configure("TLabel", background=APP_PANEL, foreground="#1F1F1F")
        for widget_name in (
            "book_list", "chapter_list", "result_list", "theme_list", "people_list",
            "bookmark_list", "selected_text", "teaching_text", "cross_list",
            "dashboard_text", "language_text", "map_text", "passage_people_list",
            "map_list", "related_hymn_list", "commentary_text", "note_text",
        ):
            widget = getattr(self, widget_name, None)
            if not widget:
                continue
            try:
                widget.configure(bg=bg, fg=fg)
            except Exception as exc:
                logger.debug("Widget %s does not support bg/fg configuration: %s", widget_name, exc)
            try:
                widget.configure(disabledforeground=fg)
            except Exception as exc:
                logger.debug("Widget %s does not support disabledforeground configuration: %s", widget_name, exc)
        self.reader.configure(
            bg=bg,
            fg=fg,
            insertbackground=fg,
            font=(font_name, font_size),
        )
        self.reader.tag_configure("selected", foreground="#005a9e", underline=True)
        self.reader.tag_configure("highlight", background=highlight)

    def save_settings(self):
        write_settings(self.settings)
        self.apply_reader_settings()
        if is_range_reference(self.selected_ref):
            self.render_passage_range(self.selected_ref)
        else:
            self.render_chapter()

    def open_settings_window(self):
        SettingsWindow(self)

    def open_help_window(self):
        HelpWindow(self)

    def open_help_document(self, filename):
        path = APP_DIR / filename
        if not path.exists():
            messagebox.showinfo("Help", f"Could not find {filename}.")
            return
        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Help", f"Could not open {filename}:\n{exc}")

    def current_highlight_key(self):
        return f"{self.translation}|{self.current_book}|{self.current_chapter}"

    def save_reader_highlights(self):
        ranges = []
        tag_ranges = self.reader.tag_ranges("highlight")
        for index in range(0, len(tag_ranges), 2):
            ranges.append({
                "start": self.reader.index(tag_ranges[index]),
                "end": self.reader.index(tag_ranges[index + 1]),
            })
        key = self.current_highlight_key()
        if ranges:
            self.highlights[key] = ranges
        else:
            self.highlights.pop(key, None)
        write_highlights(self.highlights)

    def apply_saved_highlights(self):
        key = self.current_highlight_key()
        for item in self.highlights.get(key, []):
            start = item.get("start")
            end = item.get("end")
            if not start or not end:
                continue
            try:
                if self.reader.compare(start, "<", "end") and self.reader.compare(end, "<=", "end") and self.reader.compare(start, "<", end):
                    self.reader.tag_add("highlight", start, end)
            except tk.TclError:
                continue

    def apply_highlight(self, event=None):
        """Apply highlight to selected text (Ctrl+H)"""
        try:
            self.reader.configure(state="normal")
            sel_start = self.reader.index("sel.first")
            sel_end = self.reader.index("sel.last")
            self.reader.tag_add("highlight", sel_start, sel_end)
            self.save_reader_highlights()
            self.reader.configure(state="disabled")
            return "break"  # Prevent default behavior
        except tk.TclError:
            # No selection
            return "break"

    def remove_highlight(self, event=None):
        """Remove highlight from selected text (Ctrl+U)"""
        try:
            sel_start = self.reader.index("sel.first")
            sel_end = self.reader.index("sel.last")
            self.remove_highlight_range(sel_start, sel_end)
            return "break"  # Prevent default behavior
        except tk.TclError:
            # No selection
            return "break"

    def remove_highlight_range(self, sel_start, sel_end):
        """Remove highlight from a specific reader range."""
        self.reader.configure(state="normal")
        try:
            self.reader.tag_remove("highlight", sel_start, sel_end)
            self.save_reader_highlights()
            self.app_status_var.set("Highlight removed.")
        finally:
            self.reader.configure(state="disabled")

    def clear_chapter_highlights(self):
        """Remove every highlight visible in the current reader chapter."""
        self.reader.configure(state="normal")
        try:
            self.reader.tag_remove("highlight", "1.0", "end")
            self.save_reader_highlights()
            self.app_status_var.set("Highlights cleared for this chapter.")
        finally:
            self.reader.configure(state="disabled")

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the reader text widget"""
        try:
            if event.num == 5 or event.delta < 0:
                # Scroll down
                self.reader.yview_scroll(3, "units")
            elif event.num == 4 or event.delta > 0:
                # Scroll up
                self.reader.yview_scroll(-3, "units")
            return "break"
        except Exception as exc:
            logger.debug("Reader mousewheel event could not be handled: %s", exc)
            return "break"

    def _on_canvas_mousewheel(self, event, canvas):
        """Handle mouse wheel scrolling for the right panel canvas"""
        try:
            if event.num == 5 or event.delta < 0:
                # Scroll down
                canvas.yview_scroll(3, "units")
            elif event.num == 4 or event.delta > 0:
                # Scroll up
                canvas.yview_scroll(-3, "units")
            return "break"
        except Exception as exc:
            logger.debug("Canvas mousewheel event could not be handled: %s", exc)
            return "break"

    def show_reader_context_menu(self, event):
        """Show right-click context menu for reader text"""
        try:
            # Check if there's selected text
            sel_start = self.reader.index("sel.first")
            sel_end = self.reader.index("sel.last")
            selected_text = self.reader.get(sel_start, sel_end)
            
            # Create context menu
            context_menu = tk.Menu(self.reader, tearoff=0)
            context_menu.add_command(
                label="📋 Copy", 
                command=lambda: self.copy_selected_text(selected_text)
            )
            context_menu.add_command(
                label="🟡 Highlight", 
                command=lambda: self.highlight_from_context_menu(sel_start, sel_end)
            )
            context_menu.add_command(
                label="🟡 Highlight & Copy", 
                command=lambda: self.highlight_and_copy(sel_start, sel_end, selected_text)
            )
            context_menu.add_command(
                label="Remove Highlight",
                command=lambda: self.remove_highlight_range(sel_start, sel_end)
            )
            context_menu.add_command(
                label="Clear Chapter Highlights",
                command=self.clear_chapter_highlights
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="📝 Add to Journal", 
                command=lambda: self.add_selection_to_journal(selected_text)
            )
            
            # Display context menu at mouse position
            context_menu.tk_popup(event.x_root, event.y_root)
            
        except tk.TclError:
            # No text selected, show basic menu
            context_menu = tk.Menu(self.reader, tearoff=0)
            context_menu.add_command(label="(Select text first)", state="disabled")
            context_menu.tk_popup(event.x_root, event.y_root)
        
        return "break"
    
    def copy_selected_text(self, text):
        """Copy selected text to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        messagebox.showinfo("Copy", "Text copied to clipboard!")
    
    def highlight_from_context_menu(self, sel_start, sel_end):
        """Highlight selected text from context menu"""
        # Enable widget temporarily
        self.reader.configure(state="normal")
        
        # Show highlight color selector
        highlight_window = tk.Toplevel(self)
        highlight_window.title("Choose Highlight Color")
        highlight_window.geometry("300x250")
        
        ttk.Label(highlight_window, text="Select highlight color:", font=("Arial", 10)).pack(pady=10)
        
        colors = {
            "🟡 Yellow (Important)": "#ffff00",
            "🔴 Red (Questions)": "#ff9999",
            "🔵 Blue (Promises)": "#99ccff",
            "🟢 Green (Commands)": "#99ff99",
            "🟠 Orange (Prophecy)": "#ffcc99",
        }
        
        for label, color in colors.items():
            btn_frame = tk.Frame(highlight_window, bg=color, height=40)
            btn_frame.pack(fill="x", padx=10, pady=5)
            btn = tk.Button(
                btn_frame, 
                text=label, 
                bg=color, 
                command=lambda c=color: self.apply_highlight_color(sel_start, sel_end, c, highlight_window)
            )
            btn.pack(fill="both", expand=True)
        
        # Disable widget again
        self.reader.configure(state="disabled")
    
    def apply_highlight_color(self, sel_start, sel_end, color, window):
        """Apply highlight color to selected text"""
        self.reader.configure(state="normal")
        self.settings["highlight_bg"] = color
        write_settings(self.settings)
        self.reader.tag_configure("highlight", background=color)
        self.reader.tag_add("highlight", sel_start, sel_end)
        self.save_reader_highlights()
        self.reader.configure(state="disabled")
        window.destroy()
        self.library_status.set("Highlighted selected text.")
    
    def highlight_and_copy(self, sel_start, sel_end, selected_text):
        """Highlight and copy selected text"""
        # Copy first
        self.copy_selected_text(selected_text)
        
        # Then highlight
        self.highlight_from_context_menu(sel_start, sel_end)
    
    def add_selection_to_journal(self, selected_text):
        """Add selected text to journal entry"""
        journal_window = JournalWindow(self, self.selected_ref, self.passage_text(self.selected_ref))
        # Insert selected text into journal
        journal_window.reflection_text.insert("1.0", f"Selected: {selected_text}\n\n")
        journal_window.reflection_text.focus()
    
    def apply_dark_mode(self):
        """Apply dark mode theme"""
        self.settings["reader_bg"] = "#1e1e1e"
        self.settings["reader_fg"] = "#e0e0e0"
        self.settings["highlight_bg"] = "#3d5a3d"
        self.save_settings()
    
    def apply_light_mode(self):
        """Apply light mode theme"""
        self.settings["reader_bg"] = "#fbfcfd"
        self.settings["reader_fg"] = "#1F1F1F"
        self.settings["highlight_bg"] = "#edf6f5"
        self.save_settings()

    def render_all(self):
        self.render_books()
        self.render_chapters()
        self.render_themes()
        self.render_people()
        self.render_bookmarks()
        self.render_chapter()
        self.update_history_buttons()

    def render_books(self):
        self.book_list.delete(0, "end")
        for book in self.available_books():
            self.book_list.insert("end", book)
        self.select_list_value(self.book_list, self.current_book)

    def render_chapters(self):
        self.chapter_list.delete(0, "end")

        chapter_count = self.chapter_count()
        chapters = list(range(1, chapter_count + 1))
        for chapter in chapters:
            suffix = "" if self.chapter_is_available(self.current_book, chapter) else " (online)"
            self.chapter_list.insert("end", f"Chapter {chapter}{suffix}")

        if self.current_chapter in chapters:
            self.chapter_list.selection_set(chapters.index(self.current_chapter))

    def render_themes(self):
        if not hasattr(self, "theme_list"):
            return
        self.theme_suggestion_targets = []
        self.theme_list.delete(0, "end")
        suggestions = self.smart_theme_suggestions(self.selected_ref)
        if suggestions:
            self.theme_list.insert("end", "Smart Suggestions")
            self.theme_suggestion_targets.append(None)
            for item in suggestions[:14]:
                self.theme_list.insert("end", f"{item['label']} - {item['reason']}")
                self.theme_suggestion_targets.append(item)
            self.theme_list.insert("end", "Curated Themes")
            self.theme_suggestion_targets.append(None)
        for theme, refs in THEMES.items():
            self.theme_list.insert("end", f"{theme} ({len(refs)})")
            self.theme_suggestion_targets.append({"kind": "curated", "theme": theme, "refs": refs})

    def current_chapter_text(self):
        verses = BIBLE.get(self.translation, {}).get(self.current_book, {}).get(self.current_chapter, [])
        if self.translation == "NIV" and len(verses) == 1:
            return format_niv_chapter_text(verses[0])
        return " ".join(str(verse) for verse in verses)

    def smart_theme_suggestions(self, ref):
        suggestions = []
        seen = set()

        def add(label, reason, target=None, kind="suggestion", score=1):
            key = label.lower()
            if key in seen:
                return
            seen.add(key)
            suggestions.append({"label": label, "reason": reason, "target": target, "kind": kind, "score": score})

        parts = reference_parts(ref)
        book = parts[0] if parts else self.current_book
        chapter = parts[1] if parts else self.current_chapter
        chapter_text = self.current_chapter_text()
        passage_text = self.passage_text(ref)
        haystack = f"{book} {chapter} {chapter_text} {passage_text}".lower()

        for theme in themes_for_reference(ref):
            refs = THEMES.get(theme, [])
            add(theme, "Curated theme linked to this passage", refs[0] if refs else ref, "curated-hit", 12)

        for person in self.people_for_reference(ref)[:6]:
            person_refs = PEOPLE.get(person, {}).get("references", [])
            add(person, "Person connected to this passage", person_refs[0] if person_refs else ref, "person", 10)

        for map_item in maps_for_reference(ref)[:5]:
            target = (map_item.get("related_passages") or [ref])[0]
            add(map_item.get("title", "Place / Map"), "Place or geography connection", target, "map", 8)

        for concept in self.concepts:
            refs = concept.get("references", [])
            ref_set = set(refs_for_study_entry(ref))
            concept_text = " ".join([
                concept.get("name", ""),
                concept.get("category", ""),
                concept.get("summary", ""),
                concept.get("notes", ""),
            ]).lower()
            if ref_set.intersection(refs):
                add(concept.get("name", ""), "Concept directly linked to this passage", refs[0] if refs else ref, "concept", 11)
            elif any(token in haystack for token in re.findall(r"[a-z]{5,}", concept_text)[:12]):
                add(concept.get("name", ""), "Concept keywords appear in this chapter", refs[0] if refs else ref, "concept", 4)

        book_groups = [
            ({"Genesis"}, "Creation / Patriarchs", "Book context", "Genesis 12:1"),
            ({"Exodus", "Leviticus", "Numbers", "Deuteronomy"}, "Covenant and Wilderness", "Torah context", "Deuteronomy 6:4"),
            ({"Joshua", "Judges", "Ruth"}, "Land, Judges, and Covenant Faithfulness", "Historical context", "Joshua 1:6"),
            ({"1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles"}, "Kingship and Kingdom", "Monarchy context", "2 Samuel 7:12"),
            ({"Ezra", "Nehemiah", "Esther"}, "Exile and Return", "Restoration context", "Ezra 1:1"),
            ({"Psalm", "Proverbs", "Job", "Ecclesiastes", "Song of Solomon"}, "Wisdom and Worship", "Wisdom/worship context", "Psalm 1:1"),
            ({"Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel"}, "Prophets, Exile, and Hope", "Prophetic context", "Isaiah 40:1"),
            ({"Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"}, "Minor Prophets", "Prophetic context", "Micah 6:8"),
            ({"Matthew", "Mark", "Luke", "John"}, "Life and Teaching of Jesus", "Gospel context", "John 1:14"),
            ({"Acts"}, "Early Church Mission", "Acts context", "Acts 1:8"),
            ({"Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians"}, "Pauline Theology", "Epistle context", "Romans 8:1"),
            ({"Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"}, "Church, Endurance, and Hope", "General epistle/apocalypse context", "Revelation 21:1"),
        ]
        for books, label, reason, target in book_groups:
            if book in books:
                add(label, reason, target, "book-context", 6)
                break

        keyword_rules = [
            ("Promised Land / Inheritance", ["land", "inherit", "possession", "jordan", "canaan", "bashan", "gilead"], "Joshua 1:6"),
            ("Leadership Transition", ["joshua", "charge", "command", "lead", "successor"], "Deuteronomy 31:7"),
            ("Prayer and God's Answer", ["pray", "besought", "plead", "ask", "answered", "enough"], "Deuteronomy 3:23"),
            ("Conquest and Conflict", ["king", "battle", "smote", "defeat", "giants", "army", "war"], "Joshua 6:2"),
            ("Covenant Obedience", ["command", "statute", "obey", "covenant", "law", "keep"], "Deuteronomy 6:4"),
            ("Wilderness Testing", ["wilderness", "wander", "forty", "murmur", "test"], "Deuteronomy 8:2"),
            ("Temple and Worship", ["temple", "altar", "sacrifice", "priest", "offering", "worship"], "1 Kings 8:10"),
            ("Messiah and Redemption", ["messiah", "christ", "redeem", "savior", "salvation", "lamb"], "Isaiah 53:5"),
            ("Kingdom of God", ["kingdom", "reign", "throne", "king"], "Matthew 6:33"),
            ("Exile and Restoration", ["exile", "captivity", "return", "restore", "remnant"], "Jeremiah 29:10"),
            ("Faith and Trust", ["faith", "believe", "trust", "hope"], "Hebrews 11:1"),
        ]
        for label, words, target in keyword_rules:
            hits = [word for word in words if re.search(rf"\b{re.escape(word)}\w*\b", haystack)]
            if hits:
                add(label, "Keywords: " + ", ".join(hits[:4]), target, "keyword", 7 + len(hits))

        stop_words = {
            "shall", "unto", "that", "with", "they", "them", "were", "from", "have", "this", "their", "which",
            "said", "lord", "will", "your", "thou", "thee", "upon", "when", "then", "there", "also", "into",
        }
        words = re.findall(r"\b[A-Za-z]{5,}\b", chapter_text.lower())
        counts = {}
        for word in words:
            if word in stop_words:
                continue
            counts[word] = counts.get(word, 0) + 1
        repeated = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
        if repeated:
            add("Repeated Words", ", ".join(f"{word} ({count})" for word, count in repeated), ref, "word-pattern", 5)

        suggestions.sort(key=lambda item: (-item["score"], item["label"]))
        return suggestions

    def render_people(self):
        if not hasattr(self, "people_list"):
            return
        query = self.people_search_var.get().strip().lower() if hasattr(self, "people_search_var") else ""
        self.visible_people = []
        self.people_list.delete(0, "end")
        for name in sorted(PEOPLE):
            entry = PEOPLE[name]
            haystack = " ".join([
                name,
                entry.get("canon", ""),
                entry.get("category", ""),
                " ".join(entry.get("roles", [])),
                " ".join(entry.get("aliases", [])),
                entry.get("summary", ""),
                entry.get("article", ""),
            ]).lower()
            if query and query not in haystack:
                continue
            self.visible_people.append(name)
            roles = ", ".join(entry.get("roles", [])[:2])
            suffix = f" - {roles}" if roles else ""
            self.people_list.insert("end", f"{name}{suffix}")

    def people_for_reference(self, ref):
        names = set()
        entry = STUDY.get(ref, {})
        names.update(entry.get("people", []))
        range_parts = reference_range_parts(ref)
        refs_to_check = []
        if range_parts:
            book, chapter, start, end = range_parts
            refs_to_check = [f"{book} {chapter}:{verse}" for verse in range(start, end + 1)]
        else:
            refs_to_check = [ref]
        for name, person in PEOPLE.items():
            person_refs = set(person.get("references", []))
            if person_refs.intersection(refs_to_check):
                names.add(name)
            text = self.passage_text(ref).lower()
            if name.lower() in text:
                names.add(name)
        return sorted(name for name in names if name in PEOPLE)

    def dashboard_summary(self, ref):
        entry = STUDY.get(ref, {})
        lines = []
        themes = themes_for_reference(ref)
        if themes:
            lines.append("Themes: " + ", ".join(themes))
        smart = self.smart_theme_suggestions(ref)
        if smart:
            lines.append("Smart suggestions:\n" + "\n".join(f"- {item['label']}: {item['reason']}" for item in smart[:6]))
        concept_names = []
        ref_set = set(refs_for_study_entry(ref))
        for concept in self.concepts:
            if ref_set.intersection(concept.get("references", [])):
                concept_names.append(concept.get("name", ""))
        if concept_names:
            lines.append("Concepts: " + ", ".join(concept_names))
        language = entry.get("language", [])
        if language:
            word_lines = []
            for word, original, note in language:
                hit_count = len(word_occurrences(BIBLE.get(self.translation, {}), word))
                word_lines.append(f"{word} / {original}: {hit_count} verse hits")
            lines.append("Word hits:\n" + "\n".join(word_lines))
        strongs_text = strongs_text_for_reference(ref)
        if strongs_text:
            lines.append("Strong's tags:\n" + strongs_text[:450])
        warnings = original_language_warnings()
        if warnings:
            lines.append("Language cautions:\nSame English word appears with multiple originals in your notes:\n" + "\n".join(warnings[:3]))
        edges = cross_reference_edges(ref)
        if edges:
            lines.append("Cross-reference links: " + str(len(edges)))
        if not lines:
            lines.append("No dashboard links have been added for this passage yet.")
        return "\n\n".join(lines)

    def render_dashboard(self, ref):
        if hasattr(self, "dashboard_text"):
            self.set_text(self.dashboard_text, self.dashboard_summary(ref))
        if hasattr(self, "commentary_text"):
            commentary, path = commentary_for_reference(ref)
            if commentary:
                self.set_text(self.commentary_text, f"{path.name}\n\n{commentary}")
            else:
                self.set_text(
                    self.commentary_text,
                    f"No local commentary file found.\n\nAdd markdown files in:\n{COMMENTARY_DIR}",
                )

    def render_passage_people(self, ref):
        if not hasattr(self, "passage_people_list"):
            return
        self.passage_people = self.people_for_reference(ref)
        self.passage_people_list.delete(0, "end")
        if not self.passage_people:
            self.passage_people_list.insert("end", "No people tagged yet")
            return
        for name in self.passage_people:
            person = PEOPLE.get(name, {})
            role = ", ".join(person.get("roles", [])[:2])
            self.passage_people_list.insert("end", f"{name} - {role}" if role else name)

    def render_passage_maps(self, ref):
        if not hasattr(self, "map_list"):
            return
        self.passage_maps = maps_for_reference(ref)
        self.map_list.delete(0, "end")
        if not self.passage_maps:
            self.map_list.insert("end", "No related maps found")
            return
        for item in self.passage_maps[:12]:
            image_marker = "image" if item.get("local_image") else "metadata"
            self.map_list.insert("end", f"{item.get('title', '')} ({image_marker})")

    def render_related_hymns(self, ref):
        if not hasattr(self, "related_hymn_list"):
            return
        self.related_hymn_list.delete(0, "end")
        hymns = self.hymn_links.get(ref, [])
        if not hymns:
            self.related_hymn_list.insert("end", "No hymns linked yet")
            return
        for hymn in hymns:
            number = f"{hymn.get('number')}. " if hymn.get("number") else ""
            self.related_hymn_list.insert("end", f"{number}{hymn.get('title', '')} ({hymn.get('hymnal', '')})")

    def annotation_marker_for_ref(self, ref):
        markers = []
        if self.notes.get(ref):
            markers.append("N")
        if any(entry.get("reference") == ref for entry in self.journal_entries):
            markers.append("J")
        if self.worksheets.get(ref):
            markers.append("W")
        if self.hymn_links.get(ref):
            markers.append("H")
        tags = getattr(self, "verse_tags", {}).get(ref, [])
        if tags:
            markers.append("T")
        return f" [{' '.join(markers)}]" if markers else ""

    def render_bookmarks(self):
        if not hasattr(self, "bookmark_list"):
            return
        self.bookmark_list.delete(0, "end")
        for bookmark in self.bookmarks:
            ref = bookmark.get("reference", "")
            note = bookmark.get("note", "")
            label = f"{ref} - {note}" if note else ref
            self.bookmark_list.insert("end", label)

    def render_chapter(self):
        self.chapter_title.configure(text=f"{self.current_book} {self.current_chapter}")
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        verses = BIBLE.get(self.translation, {}).get(self.current_book, {}).get(self.current_chapter, [])
        if not verses:
            if (self.translation, self.current_book, self.current_chapter) in self.fetching_chapters:
                message = f"Fetching {self.translation} {self.current_book} {self.current_chapter} online...\n\nThis chapter will be saved for offline reading."
            elif self.translation in ("KJV", "JPS1917"):
                message = "This chapter is not cached yet.\n\nSelect it again or use quick lookup to fetch it online and save it locally."
            else:
                message = "This chapter is not in the local library yet.\n\nUse Import JSON to add it."
            self.reader.insert("end", message)
            self.reader.configure(state="disabled")
            return
        if self.translation == "NIV" and len(verses) == 1:
            for verse_number, text in niv_chapter_segments(verses[0]):
                ref = f"{self.current_book} {self.current_chapter}:{verse_number}"
                start = self.reader.index("end")
                self.reader.insert("end", f"{verse_number}{self.annotation_marker_for_ref(ref)} ", ("verse_number",))
                self.reader.insert("end", f"{text}\n\n")
                end = self.reader.index("end")
                self.reader.tag_add(ref, start, end)
                self.reader.tag_bind(ref, "<Button-1>", lambda _event, r=ref: self.select_verse(r))
                if ref == self.selected_ref:
                    self.reader.tag_add("selected", start, end)
            self.apply_saved_highlights()
            self.reader.configure(state="disabled")
            return
        for index, text in enumerate(verses, start=1):
            ref = f"{self.current_book} {self.current_chapter}:{index}"
            start = self.reader.index("end")
            self.reader.insert("end", f"{index}{self.annotation_marker_for_ref(ref)} ", ("verse_number",))
            self.reader.insert("end", f"{text}\n\n")
            end = self.reader.index("end")
            self.reader.tag_add(ref, start, end)
            self.reader.tag_bind(ref, "<Button-1>", lambda _event, r=ref: self.select_verse(r))
            if ref == self.selected_ref:
                self.reader.tag_add("selected", start, end)
            range_parts = reference_range_parts(self.selected_ref)
            if range_parts:
                book, chapter, start_verse, end_verse = range_parts
                if book == self.current_book and chapter == self.current_chapter and start_verse <= index <= end_verse:
                    self.reader.tag_add("selected", start, end)
        self.apply_saved_highlights()
        self.reader.configure(state="disabled")

    def render_passage_range(self, ref):
        range_parts = reference_range_parts(ref)
        if not range_parts:
            return
        book, chapter, start, end = range_parts
        verses = BIBLE.get(self.translation, {}).get(book, {}).get(chapter, [])
        self.chapter_title.configure(text=f"{book} {chapter}:{start}-{end}")
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        for index in range(start, min(end, len(verses)) + 1):
            text = verses[index - 1]
            verse_ref = f"{book} {chapter}:{index}"
            verse_start = self.reader.index("end")
            self.reader.insert("end", f"{index}{self.annotation_marker_for_ref(verse_ref)} ", ("verse_number",))
            self.reader.insert("end", f"{text}\n\n")
            verse_end = self.reader.index("end")
            self.reader.tag_add("selected", verse_start, verse_end)
            self.reader.tag_add(verse_ref, verse_start, verse_end)
            self.reader.tag_bind(verse_ref, "<Button-1>", lambda _event, r=verse_ref: self.select_verse(r))
        self.apply_saved_highlights()
        self.reader.configure(state="disabled")

    def select_verse(self, ref, rerender=True):
        ref = normalized_reference(ref)
        if not self.passage_text(ref):
            return
        self.selected_ref = ref
        self.selected_label.configure(text=ref)
        self.set_text(self.selected_text, self.passage_text(ref))
        entry = STUDY.get(ref, {})
        self.set_text(self.teaching_text, entry.get("teaching", "No teaching note has been added for this verse yet."))
        self.cross_list.delete(0, "end")
        shown_refs = []
        for group, items in self.grouped_cross_references(ref).items():
            for item in items[:4]:
                target = item.get("target", "")
                if target and target not in shown_refs:
                    shown_refs.append(target)
                    self.cross_list.insert("end", target)
            if len(shown_refs) >= 12:
                break
        if not self.cross_list.size():
            self.cross_list.insert("end", "No cross references added yet")
        self.render_dashboard(ref)
        language_lines = []
        for word, original, note in entry.get("language", []):
            language_lines.append(f"{word} - {original}\n{note}")
        self.set_text(self.language_text, "\n\n".join(language_lines) or "Original language notes can be added here later.")
        related_maps = maps_for_reference(ref)
        if entry.get("map"):
            context_lines = [entry.get("map", "")]
        elif related_maps:
            titles = ", ".join(item.get("title", "") for item in related_maps[:3] if item.get("title"))
            context_lines = [f"Related map references: {titles}"]
        else:
            context_lines = ["No map reference has been added for this passage yet."]
        if entry.get("people"):
            context_lines.append(f"People: {', '.join(entry.get('people', []))}")
        places = list(entry.get("places", []))
        if not places and related_maps:
            seen_places = []
            for item in related_maps[:3]:
                for place in item.get("related_places", []):
                    if place and place not in seen_places:
                        seen_places.append(place)
            places = seen_places[:6]
        if places:
            context_lines.append(f"Places: {', '.join(places)}")
        if entry.get("timeline"):
            context_lines.append(f"Timeline: {entry.get('timeline')}")
        self.set_text(self.map_text, "\n\n".join(context_lines))
        self.render_passage_maps(ref)
        self.render_passage_people(ref)
        self.render_related_hymns(ref)
        self.loading_note = True
        self.note_text.delete("1.0", "end")
        self.note_text.insert("1.0", self.notes.get(ref, ""))
        try:
            self.note_text.edit_reset()
        except tk.TclError:
            pass
        self.loading_note = False
        self.note_status_var.set("Saved note attached to this passage." if self.notes.get(ref) else "No saved note for this passage yet.")
        if rerender:
            range_parts = reference_range_parts(ref)
            if range_parts:
                self.render_passage_range(ref)
            else:
                self.render_chapter()

    def set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def reference_parts(self, ref):
        return reference_parts(ref)

    def verse_text(self, ref):
        cached = self.lookup_cache.get_passage(self.translation, f"verse:{ref}")
        if cached is not None:
            return cached
        parts = self.reference_parts(ref)
        if not parts:
            return ""
        book, chapter, verse = parts
        verses = BIBLE.get(self.translation, {}).get(book, {}).get(chapter, [])
        if self.translation == "NIV" and len(verses) == 1:
            if verse <= 1:
                return self.lookup_cache.set_passage(self.translation, f"verse:{ref}", format_niv_chapter_text(verses[0]))
            for verse_number, verse_text in niv_chapter_segments(verses[0]):
                if verse_number == verse:
                    return self.lookup_cache.set_passage(self.translation, f"verse:{ref}", verse_text)
            return self.lookup_cache.set_passage(self.translation, f"verse:{ref}", format_niv_chapter_text(verses[0]))
        text = verses[verse - 1] if verse > 0 and verse <= len(verses) else ""
        return self.lookup_cache.set_passage(self.translation, f"verse:{ref}", text)

    def passage_text(self, ref):
        cached = self.lookup_cache.get_passage(self.translation, f"passage:{ref}")
        if cached is not None:
            return cached
        range_parts = reference_range_parts(ref)
        if range_parts:
            book, chapter, start, end = range_parts
            verses = BIBLE.get(self.translation, {}).get(book, {}).get(chapter, [])
            if self.translation == "NIV" and len(verses) == 1:
                lines = [
                    f"{verse_number}. {verse_text}"
                    for verse_number, verse_text in niv_chapter_segments(verses[0])
                    if start <= verse_number <= end
                ]
                text = "\n\n".join(lines) or format_niv_chapter_text(verses[0])
                return self.lookup_cache.set_passage(self.translation, f"passage:{ref}", text)
            if start > len(verses):
                return ""
            lines = []
            for index in range(start, min(end, len(verses)) + 1):
                lines.append(f"{index}. {verses[index - 1]}")
            return self.lookup_cache.set_passage(self.translation, f"passage:{ref}", "\n\n".join(lines))
        return self.lookup_cache.set_passage(self.translation, f"passage:{ref}", self.verse_text(ref))

    def chapter_text(self, ref):
        parts = reference_parts(ref)
        if not parts:
            return self.passage_text(ref)
        book, chapter, _verse = parts
        cache_key = f"chapter:{book} {chapter}"
        cached = self.lookup_cache.get_passage(self.translation, cache_key)
        if cached is not None:
            return cached
        verses = BIBLE.get(self.translation, {}).get(book, {}).get(chapter, [])
        if self.translation == "NIV" and len(verses) == 1:
            text = format_niv_chapter_text(verses[0])
        else:
            text = "\n\n".join(f"{index}. {verse}" for index, verse in enumerate(verses, start=1) if verse)
        return self.lookup_cache.set_passage(self.translation, cache_key, text)

    def all_references(self):
        cached = self.lookup_cache.get_references(self.translation)
        if cached is not None:
            return iter(cached)
        references = []
        for book, chapters in BIBLE[self.translation].items():
            for chapter, verses in chapters.items():
                for index, text in enumerate(verses, start=1):
                    references.append((f"{book} {chapter}:{index}", text))
        self.lookup_cache.set_references(self.translation, references)
        return iter(references)

    def remember_current_reference(self):
        if self.selected_ref and self.passage_text(self.selected_ref):
            return self.selected_ref
        return ""

    def update_history_buttons(self):
        if hasattr(self, "back_button"):
            self.back_button.configure(state="normal" if self.back_stack else "disabled")
        if hasattr(self, "forward_button"):
            self.forward_button.configure(state="normal" if self.forward_stack else "disabled")

    def go_back(self):
        if not self.back_stack:
            return
        current = self.remember_current_reference()
        target = self.back_stack.pop()
        if current:
            self.forward_stack.append(current)
        self.open_reference(target, add_history=False)

    def go_forward(self):
        if not self.forward_stack:
            return
        current = self.remember_current_reference()
        target = self.forward_stack.pop()
        if current:
            self.back_stack.append(current)
        self.open_reference(target, add_history=False)

    def record_history(self, next_ref):
        current = self.remember_current_reference()
        if current and current != next_ref:
            self.back_stack.append(current)
            self.forward_stack.clear()
            self.update_history_buttons()

    def open_reference(self, ref, add_history=True):
        range_parts = reference_range_parts(ref)
        if range_parts:
            book, chapter, start, end = range_parts
            normalized = f"{book} {chapter}:{start}-{end}"
            if book not in BIBLE.get(self.translation, {}) or chapter not in BIBLE.get(self.translation, {}).get(book, {}):
                if self.translation in ("KJV", "JPS1917"):
                    if add_history:
                        self.record_history(normalized)
                    self.request_chapter_fetch(book, chapter, start, normalized)
                    return
                messagebox.showinfo("Passage Lookup", "That passage is not in the local library yet.")
                return
            if not self.passage_text(normalized):
                messagebox.showinfo("Passage Lookup", f"{book} {chapter} does not include that verse range in the local library.")
                return
            if add_history:
                self.record_history(normalized)
            self.current_book = book
            self.current_chapter = chapter
            self.selected_ref = normalized
            self.remember_recent_reference(normalized)
            self.render_all()
            self.select_verse(normalized, rerender=False)
            self.render_passage_range(normalized)
            self.update_history_buttons()
            return

        parts = self.reference_parts(ref)
        if not parts:
            messagebox.showinfo("Passage Lookup", "Use a reference like John 1:1 or Psalm 23.")
            return
        book, chapter, verse = parts
        if book not in BIBLE.get(self.translation, {}) or chapter not in BIBLE.get(self.translation, {}).get(book, {}):
            if self.translation in ("KJV", "JPS1917"):
                if add_history:
                    self.record_history(f"{book} {chapter}:{verse}")
                self.request_chapter_fetch(book, chapter, verse)
                return
            messagebox.showinfo(
                "Passage Lookup",
                "That passage is not in the local library yet.\n\nUse Download Full KJV or Import JSON to add more chapters.",
            )
            return
        if not self.verse_text(f"{book} {chapter}:{verse}"):
            messagebox.showinfo("Passage Lookup", f"{book} {chapter} does not have verse {verse} in the local library.")
            return
        next_ref = f"{book} {chapter}:{verse}"
        if add_history:
            self.record_history(next_ref)
        self.current_book = book
        self.current_chapter = chapter
        self.selected_ref = next_ref
        self.remember_recent_reference(next_ref)
        self.render_all()
        self.select_verse(self.selected_ref)
        self.update_history_buttons()

    def open_lookup(self):
        self.open_reference(self.lookup_var.get().strip())

    def search_word(self):
        query = self.search_var.get().strip()
        self.result_list.delete(0, "end")
        self.search_refs = []
        if not query:
            return
        selected_range = self.search_range_var.get() if hasattr(self, "search_range_var") else "Whole Bible"
        books = SEARCH_RANGES.get(selected_range)
        if books == "current_book":
            books = {self.current_book}
        sort_mode = self.search_sort_var.get() if hasattr(self, "search_sort_var") else "Book order"
        results = search_bible(
            BIBLE.get(self.translation, {}),
            query,
            exact_phrase=self.search_exact_var.get() if hasattr(self, "search_exact_var") else False,
            whole_word=self.search_whole_word_var.get() if hasattr(self, "search_whole_word_var") else False,
            books=books,
            sort_mode=sort_mode,
            context=self.search_context_var.get() if hasattr(self, "search_context_var") else False,
        )
        for item in results[:500]:
            ref = item["reference"]
            self.search_refs.append(ref)
            count_label = f" ({item['count']}x)" if item["count"] > 1 else ""
            self.result_list.insert("end", f"{ref}{count_label} - {item['preview'][:90]}")
        if len(results) > 500:
            self.result_list.insert("end", f"...showing first 500 of {len(results)} matches")
        if not self.search_refs:
            self.result_list.insert("end", "No matches in the local library")

    def save_note(self):
        self.notes[self.selected_ref] = self.note_text.get("1.0", "end").strip()
        if not self.notes[self.selected_ref]:
            self.notes.pop(self.selected_ref, None)
        write_notes(self.notes)
        self.note_status_var.set("Saved note attached to this passage." if self.notes.get(self.selected_ref) else "No saved note for this passage yet.")

    def on_note_changed(self, _event=None):
        if self.loading_note:
            return
        self.note_status_var.set("Unsaved changes...")
        if self.autosave_after_id:
            self.after_cancel(self.autosave_after_id)
        self.autosave_after_id = self.after(1200, self.auto_save_note)

    def auto_save_note(self):
        self.autosave_after_id = None
        self.save_note()
        if self.notes.get(self.selected_ref):
            saved_at = datetime.now().strftime("%I:%M %p").lstrip("0")
            self.note_status_var.set(f"Auto-saved at {saved_at}.")

    def clear_note(self):
        self.notes.pop(self.selected_ref, None)
        write_notes(self.notes)
        self.note_text.delete("1.0", "end")
        try:
            self.note_text.edit_reset()
        except tk.TclError:
            pass
        self.note_status_var.set("No saved note for this passage yet.")

    def undo_note(self):
        if not hasattr(self, "note_text"):
            return "break"
        try:
            self.note_text.edit_undo()
            self.note_status_var.set("Undid last note edit.")
        except tk.TclError:
            self.note_status_var.set("Nothing to undo.")
        return "break"

    def redo_note(self):
        if not hasattr(self, "note_text"):
            return "break"
        try:
            self.note_text.edit_redo()
            self.note_status_var.set("Redid note edit.")
        except tk.TclError:
            self.note_status_var.set("Nothing to redo.")
        return "break"

    def open_journal_window(self):
        JournalWindow(self, self.selected_ref, self.passage_text(self.selected_ref))
    
    def open_tag_window(self):
        """Open tag management window"""
        TagWindow(self)
    
    def open_word_study_window(self):
        """Open word study window"""
        WordStudyWindow(self)
    
    def open_translation_comparison_window(self):
        """Open side-by-side translation comparison window"""
        TranslationComparisonWindow(self)

    def open_cross_reference_graph(self):
        CrossReferenceGraphWindow(self, cross_reference_edges)

    def open_study_sessions_window(self):
        StudySessionsWindow(self)

    def open_reading_plans_window(self):
        ReadingPlansWindow(self)

    def add_current_ref_to_session(self):
        if not self.study_sessions:
            name = simpledialog.askstring("Study Session", "Name this study session:", parent=self)
            if not name:
                return
            self.study_sessions.append({
                "name": name.strip(),
                "created": datetime.now().isoformat(timespec="seconds"),
                "references": [],
                "notes": "",
            })
        choices = [session["name"] for session in self.study_sessions]
        name = simpledialog.askstring(
            "Study Session",
            "Add to which session?\n\n" + "\n".join(choices),
            initialvalue=choices[0],
            parent=self,
        )
        if not name:
            return
        session = next((item for item in self.study_sessions if item["name"].lower() == name.strip().lower()), None)
        if not session:
            session = {"name": name.strip(), "created": datetime.now().isoformat(timespec="seconds"), "references": [], "notes": ""}
            self.study_sessions.append(session)
        if self.selected_ref not in session["references"]:
            session["references"].append(self.selected_ref)
        write_study_sessions(self.study_sessions)
        self.library_status.set(f"Added {self.selected_ref} to {session['name']}.")

    def import_commentary_file(self):
        COMMENTARY_DIR.mkdir(parents=True, exist_ok=True)
        source = filedialog.askopenfilename(
            parent=self,
            title="Import Markdown Commentary",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not source:
            return
        target_name = simpledialog.askstring(
            "Commentary Filename",
            "Save commentary as a reference-based filename, for example John 3.md or John 3 16.md:",
            initialvalue=f"{self.current_book} {self.current_chapter}.md",
            parent=self,
        )
        if not target_name:
            return
        if not target_name.lower().endswith(".md"):
            target_name += ".md"
        target = COMMENTARY_DIR / re.sub(r'[<>:"/\\|?*]+', "-", target_name)
        shutil.copyfile(source, target)
        self.render_dashboard(self.selected_ref)
        self.library_status.set(f"Imported commentary: {target.name}")

    def save_web_commentary(self, url, reference_name):
        COMMENTARY_DIR.mkdir(parents=True, exist_ok=True)
        url = str(url or "").strip()
        if not re.match(r"^https?://", url, flags=re.I):
            raise ValueError("Enter a full web address beginning with http:// or https://.")

        target_name = str(reference_name or "").strip()
        if not target_name:
            target_name = f"{self.current_book} {self.current_chapter}.md"
        if not target_name.lower().endswith(".md"):
            target_name += ".md"
        target = COMMENTARY_DIR / re.sub(r'[<>:"/\\|?*]+', "-", target_name)

        request = urllib.request.Request(url, headers={"User-Agent": "BibleReferenceStudyTool/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(3_000_000)
        encoding = "utf-8"
        match = re.search(r"charset=([\w-]+)", content_type, flags=re.I)
        if match:
            encoding = match.group(1)
        html = raw.decode(encoding, errors="ignore")

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        page_title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
        parser = PlainTextHTMLParser()
        parser.feed(html)
        text = parser.text()
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 200:
            raise RuntimeError("That page did not produce enough readable text to save.")

        wrapped_lines = []
        for paragraph in re.split(r"\s{2,}", text):
            paragraph = paragraph.strip()
            if paragraph:
                wrapped_lines.extend([paragraph, ""])
        markdown = "\n".join([
            f"# {page_title}",
            "",
            f"Source: {url}",
            f"Saved: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "> Saved for personal offline study. Keep the source link with this note.",
            "",
            "## Commentary",
            "",
            "\n".join(wrapped_lines).strip(),
            "",
        ])
        target.write_text(markdown, encoding="utf-8")
        return target

    def study_packet_lines(self):
        ref = self.selected_ref
        entry = STUDY.get(ref, {})
        lines = [
            f"# Study Packet: {ref}",
            "",
            f"Created: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Passage",
            "",
            self.passage_text(ref) or "No passage text available.",
            "",
            "## Translation Comparison",
            "",
        ]
        for code in sorted(BIBLE):
            text = verse_text_from_translation(code, ref)
            if text:
                lines.extend([f"### {code}", "", text, ""])
        lines.extend(["## Cross References", ""])
        cross_refs = entry.get("cross", [])
        lines.extend([f"- {cross_ref}: {self.verse_text(cross_ref)}" for cross_ref in cross_refs] or ["No cross references added."])
        lines.extend(["", "## Themes", ""])
        lines.extend([f"- {theme}" for theme in themes_for_reference(ref)] or ["No themes linked."])
        lines.extend(["", "## People And Places", ""])
        people = self.people_for_reference(ref)
        places = entry.get("places", [])
        lines.append("People: " + (", ".join(people) if people else "None tagged."))
        lines.append("Places: " + (", ".join(places) if places else "None tagged."))
        lines.extend(["", "## Original Language", ""])
        for word, original, note in entry.get("language", []):
            lines.extend([f"### {word} / {original}", "", note, ""])
        if not entry.get("language"):
            lines.append("No language notes added.")
        commentary, path = commentary_for_reference(ref)
        lines.extend(["", "## Local Commentary", "", commentary or "No local commentary imported."])
        lines.extend(["", "## Personal Note", "", self.notes.get(ref, "No personal note saved.")])
        lines.extend(["", "## Study Questions", ""])
        lines.extend([
            f"- What does {ref} reveal about God, people, or the covenant story?",
            "- Which repeated words or themes deserve closer study?",
            "- How do the cross references sharpen or complicate the passage?",
            "- What should I remember, believe, practice, or ask next?",
        ])
        return lines

    def export_study_packet(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_ref = re.sub(r"[^A-Za-z0-9_-]+", "-", self.selected_ref).strip("-")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        md_path = EXPORT_DIR / f"study-packet-{safe_ref}-{timestamp}.md"
        html_path = EXPORT_DIR / f"study-packet-{safe_ref}-{timestamp}.html"
        lines = self.study_packet_lines()
        md_path.write_text("\n".join(lines), encoding="utf-8")
        html_body = "\n".join(f"<p>{line}</p>" if line and not line.startswith("#") else f"<h{min(line.count('#'), 3)}>{line.lstrip('# ').strip()}</h{min(line.count('#'), 3)}>" if line.startswith("#") else "" for line in lines)
        html_path.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>{self.selected_ref}</title><style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:850px;margin:40px auto;line-height:1.55}}</style></head><body>{html_body}</body></html>", encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Saved study packet:\n{md_path}\n\n{html_path}")
    
    def show_verse_statistics(self):
        """Display verse statistics"""
        stats_text = f"""Reading Statistics:
        
Total Verses Read: {self.statistics['total_verses_read']}
Total Reading Time: {self.statistics['total_reading_time']} minutes
Highlighted Verses: {self.statistics['highlighted_verses']}
Tagged Verses: {self.statistics['tagged_verses']}

Most Highlighted Verses:
{chr(10).join(self.statistics['most_highlighted'][:5]) if self.statistics['most_highlighted'] else 'None yet'}

Most Tagged Verses:
{chr(10).join(self.statistics['most_tagged'][:5]) if self.statistics['most_tagged'] else 'None yet'}"""
        
        messagebox.showinfo("Verse Statistics", stats_text)
    
    def add_verse_tag(self, ref, tag):
        """Add a tag to a verse"""
        if ref not in self.verse_tags:
            self.verse_tags[ref] = []
        if tag not in self.verse_tags[ref]:
            self.verse_tags[ref].append(tag)
            self.statistics['tagged_verses'] = len(set(v for tags in self.verse_tags.values() for v in tags))
    
    def remove_verse_tag(self, ref, tag):
        """Remove a tag from a verse"""
        if ref in self.verse_tags and tag in self.verse_tags[ref]:
            self.verse_tags[ref].remove(tag)
    
    def add_verse_highlight(self, ref, color, category):
        """Add highlight to a verse with category"""
        self.verse_highlights[ref] = {"color": color, "category": category}
        self.statistics['highlighted_verses'] = len(self.verse_highlights)
        # Update most highlighted
        self.statistics['most_highlighted'] = sorted(
            self.verse_highlights.keys(), 
            key=lambda x: self.verse_highlights[x].get('count', 0), 
            reverse=True
        )
    
    def get_verse_by_reference(self, ref):
        """Get verse text by reference"""
        parts = self.reference_parts(ref)
        if not parts:
            return None
        book, chapter, verse = parts
        verses = BIBLE.get(self.translation, {}).get(book, {}).get(chapter, [])
        if verse > 0 and verse <= len(verses):
            return verses[verse - 1]
        return None

    def add_bookmark(self):
        ref = self.selected_ref
        if not self.passage_text(ref):
            return
        if any(bookmark.get("reference") == ref for bookmark in self.bookmarks):
            self.library_status.set(f"{ref} is already bookmarked.")
            return
        self.bookmarks.append({
            "reference": ref,
            "translation": self.translation,
            "created": datetime.now().isoformat(timespec="seconds"),
            "note": "",
        })
        write_bookmarks(self.bookmarks)
        self.render_bookmarks()
        self.library_status.set(f"Bookmarked {ref}.")

    def remove_selected_bookmark(self):
        if not self.bookmark_list.curselection():
            return
        index = self.bookmark_list.curselection()[0]
        if index >= len(self.bookmarks):
            return
        removed = self.bookmarks.pop(index)
        write_bookmarks(self.bookmarks)
        self.render_bookmarks()
        self.library_status.set(f"Removed bookmark {removed.get('reference', '')}.")

    def on_bookmark_selected(self, _event=None):
        if not self.bookmark_list.curselection():
            return
        index = self.bookmark_list.curselection()[0]
        if index < len(self.bookmarks):
            self.open_reference(self.bookmarks[index].get("reference", ""))

    def export_notes_journal(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = EXPORT_DIR / f"bible-study-export-{timestamp}.md"
        lines = [
            "# Bible Study Export",
            "",
            f"Created: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Personal Notes",
            "",
        ]
        if self.notes:
            for ref in sorted(self.notes):
                lines.extend([f"### {ref}", "", markdown_line(self.notes[ref]), ""])
        else:
            lines.extend(["No personal notes saved yet.", ""])

        lines.extend(["## Journal Entries", ""])
        if self.journal_entries:
            for entry in self.journal_entries:
                lines.extend([
                    f"### {entry.get('reference', 'Unknown reference')}",
                    "",
                    f"Created: {entry.get('created', '')}",
                    "",
                ])
                if entry.get("verse"):
                    lines.extend(["> " + markdown_line(entry.get("verse")).replace("\n", "\n> "), ""])
                if entry.get("reflection"):
                    lines.extend(["Reflection:", "", markdown_line(entry.get("reflection")), ""])
                if entry.get("prayer"):
                    lines.extend(["Prayer:", "", markdown_line(entry.get("prayer")), ""])
                if entry.get("images"):
                    lines.extend(["Images:", ""])
                    for image in entry.get("images", []):
                        lines.append(f"- {image}")
                    lines.append("")
        else:
            lines.extend(["No journal entries saved yet.", ""])

        lines.extend(["## Bookmarks", ""])
        if self.bookmarks:
            for bookmark in self.bookmarks:
                lines.append(f"- {bookmark.get('reference', '')}")
            lines.append("")
        else:
            lines.extend(["No bookmarks saved yet.", ""])

        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Export saved to:\n{path}")

    def on_book_selected(self, _event=None):
        if not self.book_list.curselection():
            return
        self.current_book = self.book_list.get(self.book_list.curselection()[0])
        self.current_book, self.current_chapter, first_verse = self.first_available_reference(self.current_book)
        self.selected_ref = f"{self.current_book} {self.current_chapter}:{first_verse}"
        if not self.chapter_is_available(self.current_book, self.current_chapter):
            self.request_chapter_fetch(self.current_book, self.current_chapter, first_verse)
            return
        self.open_reference(self.selected_ref)

    def on_translation_selected(self, _event=None):
        requested = self.translation_code_from_choice(self.translation_var.get())
        if requested == "JPS1917":
            BIBLE.setdefault("JPS1917", {})
        elif requested not in BIBLE:
            self.translation_var.set(self.translation_choice_for(self.translation))
            messagebox.showinfo(
                "Translation Not Imported",
                f"{TRANSLATION_LABELS.get(requested, requested)} is not in the local library yet.\n\n"
                "Because NIV and ESV are copyrighted, the app does not bundle their full text. "
                "Use Import JSON if you have a licensed/local copy you are allowed to use.",
            )
            return
        self.translation = requested
        self.current_book, self.current_chapter, first_verse = self.first_available_reference()
        self.selected_ref = f"{self.current_book} {self.current_chapter}:{first_verse}"
        self.render_all()
        self.select_verse(self.selected_ref)

    def on_chapter_selected(self, _event=None):
        if not self.chapter_list.curselection():
            return
        label = self.chapter_list.get(self.chapter_list.curselection()[0])
        match = re.search(r"\d+", label)
        if not match:
            return
        self.current_chapter = int(match.group(0))
        self.selected_ref = f"{self.current_book} {self.current_chapter}:1"
        if not self.chapter_is_available(self.current_book, self.current_chapter):
            self.request_chapter_fetch(self.current_book, self.current_chapter)
            return
        self.open_reference(self.selected_ref)

    def on_result_selected(self, _event=None):
        if not self.result_list.curselection() or not getattr(self, "search_refs", None):
            return
        index = self.result_list.curselection()[0]
        if index < len(self.search_refs):
            self.open_reference(self.search_refs[index])

    def on_theme_selected(self, _event=None):
        if not self.theme_list.curselection():
            return
        index = self.theme_list.curselection()[0]
        item = self.theme_suggestion_targets[index] if hasattr(self, "theme_suggestion_targets") and index < len(self.theme_suggestion_targets) else None
        if not item:
            return
        if item.get("kind") != "curated":
            target = item.get("target")
            self.result_list.delete(0, "end")
            self.search_refs = []
            self.result_list.insert("end", f"{item.get('label', '')} - {item.get('reason', '')}")
            if target and self.passage_text(target):
                self.search_refs = [target]
                self.result_list.insert("end", f"{target} - {self.passage_text(target)[:70]}")
                self.open_reference(target)
            return
        theme = item.get("theme", "")
        refs = item.get("refs", THEMES.get(theme, []))
        self.search_refs = refs
        self.result_list.delete(0, "end")
        for ref in refs:
            self.result_list.insert("end", f"{ref} - {self.verse_text(ref)[:70]}")
        if refs:
            self.open_reference(refs[0])

    def on_cross_selected(self, _event=None):
        if not self.cross_list.curselection():
            return
        ref = self.cross_list.get(self.cross_list.curselection()[0])
        if ":" in ref:
            self.open_reference(ref)

    def open_person_profile(self, name):
        if name in PEOPLE:
            PersonWindow(self, name, PEOPLE, maps_for_person, MapViewerWindow)

    def open_people_reference_window(self):
        PeopleReferenceWindow(
            self,
            PEOPLE,
            PEOPLE_REFERENCE,
            lambda app, name, people: PersonWindow(app, name, people, maps_for_person, MapViewerWindow),
        )

    def open_concept_library(self):
        ConceptLibraryWindow(self)

    def on_person_selected(self, _event=None):
        if not self.people_list.curselection() or not getattr(self, "visible_people", None):
            return
        index = self.people_list.curselection()[0]
        if index < len(self.visible_people):
            self.open_person_profile(self.visible_people[index])

    def on_passage_person_selected(self, _event=None):
        if not self.passage_people_list.curselection() or not getattr(self, "passage_people", None):
            return
        index = self.passage_people_list.curselection()[0]
        if index < len(self.passage_people):
            self.open_person_profile(self.passage_people[index])

    def on_map_selected(self, _event=None):
        self.open_selected_map()

    def open_selected_map(self):
        if not getattr(self, "passage_maps", None) or not hasattr(self, "map_list") or not self.map_list.curselection():
            return
        index = self.map_list.curselection()[0]
        if index < len(self.passage_maps):
            MapViewerWindow(self, self.passage_maps[index])

    def select_list_value(self, listbox, value):
        for index in range(listbox.size()):
            if listbox.get(index) == value:
                listbox.selection_set(index)
                listbox.see(index)
                return


class StudyDashboardWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Study Dashboard")
        self.geometry("760x640")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Dashboard", style="Title.TLabel").pack(anchor="w")
        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(8, 10))
        ttk.Button(buttons, text="Continue", command=lambda: self.app.open_reference(self.app.selected_ref)).pack(side="left")
        ttk.Button(buttons, text="Worksheet", command=self.app.open_study_worksheet).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Search Everything", command=self.app.open_search_everything).pack(side="left", padx=(8, 0))
        text = tk.Text(root, wrap="word")
        text.pack(fill="both", expand=True)
        lines = [f"Current passage: {self.app.selected_ref}", "", "Reading Plans"]
        for plan in self.app.reading_plans[:4]:
            completed = set(plan.get("completed", []))
            next_ref = next((ref for ref in plan.get("references", []) if ref not in completed), "Complete")
            lines.append(f"- {plan.get('name', '')}: {next_ref} ({len(completed)}/{len(plan.get('references', []))})")
        lines.extend(["", "Recent Passages"])
        lines.extend(f"- {item.get('reference', '')}" for item in self.app.recent_references[:8])
        lines.extend(["", "Recent Notes"])
        lines.extend(f"- {ref}: {note[:90]}" for ref, note in list(self.app.notes.items())[-8:][::-1] if note)
        lines.extend(["", "Active Sessions"])
        lines.extend(f"- {s.get('name', '')}: {len(s.get('references', []))} passages, {len(s.get('hymns', []))} hymns" for s in self.app.study_sessions[:8])
        lines.extend(["", "Recent Hymns"])
        lines.extend(f"- {h.get('number', '')} {h.get('title', '')} ({h.get('hymnal', '')})" for h in self.app.recent_hymns[:8])
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")


class PassageStudyWorksheetWindow(tk.Toplevel):
    FIELDS = [
        ("observation", "Observation"), ("interpretation", "Interpretation"),
        ("application", "Application"), ("questions", "Questions"),
        ("prayer", "Prayer"), ("related_hymn", "Related Hymn"), ("tags", "Tags"),
    ]

    def __init__(self, app, ref):
        super().__init__(app)
        self.app = app
        self.ref = normalized_reference(ref)
        self.widgets = {}
        self.title(f"Study Worksheet - {self.ref}")
        self.geometry("780x760")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Study Worksheet: {self.ref}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=self.app.passage_text(self.ref), style="Muted.TLabel", wraplength=720).pack(anchor="w", pady=(4, 10))
        data = self.app.worksheets.get(self.ref, {})
        for key, label in self.FIELDS:
            ttk.Label(root, text=label, style="Section.TLabel").pack(anchor="w", pady=(8, 0))
            widget = tk.Text(root, height=3 if key in {"related_hymn", "tags"} else 4, wrap="word")
            widget.pack(fill="x", pady=(4, 0))
            widget.insert("1.0", data.get(key, ""))
            self.widgets[key] = widget
        ttk.Button(root, text="Save Worksheet", command=self.save, style="Primary.TButton").pack(fill="x", pady=(12, 0))

    def save(self):
        self.app.worksheets[self.ref] = {key: widget.get("1.0", "end").strip() for key, widget in self.widgets.items()}
        self.app.worksheets[self.ref]["updated"] = datetime.now().isoformat(timespec="seconds")
        write_worksheets(self.app.worksheets)
        self.app.render_chapter()
        messagebox.showinfo("Study Worksheet", "Worksheet saved.")


from bible_app.ui.windows.dashboard import StudyDashboardWindow  # noqa: E402
from bible_app.ui.windows.worksheet import PassageStudyWorksheetWindow  # noqa: E402


class WebCommentaryImportWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Save Web Commentary")
        configure_window_size(self, "web_commentary_importer", "760x520", (620, 420))

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Save Web Commentary", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Paste a commentary page URL, then save a local Markdown copy attached to a passage or book.",
            style="Muted.TLabel",
            wraplength=700,
        ).pack(anchor="w", pady=(4, 12))

        ttk.Label(root, text="Web Address", style="Section.TLabel").pack(anchor="w")
        self.url_var = tk.StringVar(value="https://www.preceptaustin.org/")
        ttk.Entry(root, textvariable=self.url_var).pack(fill="x", pady=(4, 10))

        ttk.Label(root, text="Save As Commentary File", style="Section.TLabel").pack(anchor="w")
        self.filename_var = tk.StringVar(value=f"{self.app.current_book} {self.app.current_chapter}.md")
        ttk.Entry(root, textvariable=self.filename_var).pack(fill="x", pady=(4, 6))
        ttk.Label(
            root,
            text="Use names like John 3.md, John 3 16.md, Romans.md, or Genesis 1.md. The commentary panel will find these automatically.",
            style="Muted.TLabel",
            wraplength=700,
        ).pack(anchor="w", pady=(0, 12))

        self.status_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel", wraplength=700).pack(anchor="w", pady=(0, 8))

        preview = tk.Text(root, height=8, wrap="word")
        preview.pack(fill="both", expand=True, pady=(0, 10))
        preview.insert(
            "1.0",
            "Tip: Precept Austin pages are detailed and long. Save one page at a time for personal offline study, and keep the source URL with the note.",
        )
        preview.configure(state="disabled")

        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        self.save_button = ttk.Button(buttons, text="Save Local Copy", command=self.start_save, style="Primary.TButton")
        self.save_button.pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="left", padx=(8, 0))

    def start_save(self):
        url = self.url_var.get().strip()
        filename = self.filename_var.get().strip()
        self.save_button.configure(state="disabled")
        self.status_var.set("Saving web commentary...")
        runner = getattr(self.app, "background", None)
        if runner:
            runner.submit(
                lambda: self.app.save_web_commentary(url, filename),
                on_success=self.finish_save,
                on_error=self.fail_save,
            )
        else:
            threading.Thread(target=self.save_worker, args=(url, filename), daemon=True).start()

    def save_worker(self, url, filename):
        try:
            path = self.app.save_web_commentary(url, filename)
            self.after(0, lambda: self.finish_save(path))
        except Exception as exc:
            self.after(0, lambda e=exc: self.fail_save(e))

    def finish_save(self, path):
        self.save_button.configure(state="normal")
        self.status_var.set(f"Saved: {path.name}")
        self.app.render_dashboard(self.app.selected_ref)
        self.app.library_status.set(f"Saved web commentary: {path.name}")
        messagebox.showinfo("Save Web Commentary", f"Saved local commentary:\n{path}")

    def fail_save(self, error):
        self.save_button.configure(state="normal")
        self.status_var.set("Could not save that page.")
        messagebox.showerror("Save Web Commentary", str(error))


class CrossReferenceExplorerWindow(tk.Toplevel):
    def __init__(self, app, ref):
        super().__init__(app)
        self.app = app
        self.ref = normalized_reference(ref)
        self.targets = []
        self.title(f"Cross-Reference Explorer - {self.ref}")
        self.geometry("760x620")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Cross References: {self.ref}", style="Title.TLabel").pack(anchor="w")
        row = ttk.Frame(root)
        row.pack(fill="x", pady=(8, 10))
        self.target_var = tk.StringVar()
        self.reason_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.target_var, width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.reason_var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(row, text="Add Link", command=self.add_link).pack(side="left")
        self.listbox = tk.Listbox(root, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.open_selected)
        self.refresh()

    def refresh(self):
        self.targets = []
        self.listbox.delete(0, "end")
        for group, items in self.app.grouped_cross_references(self.ref).items():
            if not items:
                continue
            self.listbox.insert("end", f"== {group} ==")
            self.targets.append(None)
            for item in items:
                self.listbox.insert("end", f"{item['target']} - {item.get('reason', '')}")
                self.targets.append(item["target"])
        if not self.targets:
            self.listbox.insert("end", "No related references yet.")
            self.targets.append(None)

    def add_link(self):
        if self.app.add_user_cross_reference(self.ref, self.target_var.get(), self.reason_var.get()):
            self.target_var.set("")
            self.reason_var.set("")
            self.refresh()
        else:
            messagebox.showinfo("Cross Reference", "Use a target like John 1:1.")

    def open_selected(self, _event=None):
        if not self.listbox.curselection():
            return
        target = self.targets[self.listbox.curselection()[0]]
        if target:
            self.app.open_reference(target)


from bible_app.ui.windows.cross_reference import CrossReferenceExplorerWindow  # noqa: E402


class TimelineWindow(tk.Toplevel):
    TIMELINE = [
        ("Creation / Primeval History", "Genesis 1-11", ["Adam", "Eve", "Noah"]),
        ("Patriarchs", "Genesis 12-50", ["Abraham", "Sarah", "Isaac", "Jacob", "Joseph"]),
        ("Exodus and Wilderness", "Exodus-Deuteronomy", ["Moses", "Aaron", "Miriam"]),
        ("Conquest and Judges", "Joshua-Judges", ["Joshua", "Deborah", "Gideon", "Samson"]),
        ("United Monarchy", "1-2 Samuel, 1 Kings", ["Saul", "David", "Solomon"]),
        ("Divided Kingdom and Prophets", "Kings / Prophets", ["Elijah", "Elisha", "Isaiah", "Jeremiah"]),
        ("Exile and Return", "Daniel, Ezra, Nehemiah", ["Daniel", "Ezra", "Nehemiah", "Esther"]),
        ("Life of Jesus", "Gospels", ["Jesus", "Mary the Mother of Jesus", "Peter", "John"]),
        ("Early Church and Paul", "Acts / Epistles", ["Paul", "Barnabas", "Silas", "Timothy", "Luke"]),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Biblical Timeline")
        self.geometry("820x620")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Timeline View", style="Title.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(root, exportselection=False)
        self.listbox.pack(side="left", fill="y", pady=(10, 0))
        self.details = tk.Text(root, wrap="word")
        self.details.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(10, 0))
        for title, _refs, _people in self.TIMELINE:
            self.listbox.insert("end", title)
        self.listbox.bind("<<ListboxSelect>>", self.show)
        self.listbox.selection_set(0)
        self.show()

    def show(self, _event=None):
        if not self.listbox.curselection():
            return
        title, refs, people = self.TIMELINE[self.listbox.curselection()[0]]
        maps = sorted({item.get("title", "") for person in people for item in maps_for_person(person)[:2]})
        lines = [title, "", f"Primary texts: {refs}", "", "People:", *[f"- {person}" for person in people], "", "Related maps:", *[f"- {item}" for item in maps if item]]
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")


from bible_app.ui.windows.timeline import TimelineWindow  # noqa: E402


class SearchEverythingWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.targets = []
        self.title("Search Everything")
        self.geometry("820x640")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Search Everything", style="Title.TLabel").pack(anchor="w")
        row = ttk.Frame(root)
        row.pack(fill="x", pady=(10, 8))
        self.query_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.search())
        ttk.Button(row, text="Search", command=self.search).pack(side="left", padx=(8, 0))
        self.results = tk.Listbox(root, exportselection=False)
        self.results.pack(fill="both", expand=True)
        self.results.bind("<<ListboxSelect>>", self.open_selected)

    def add_result(self, label, target=None):
        self.results.insert("end", label)
        self.targets.append(target)

    def search(self):
        query = self.query_var.get().strip().lower()
        self.results.delete(0, "end")
        self.targets = []
        if not query:
            return
        for ref, text in self.app.all_references():
            if query in text.lower() or query in ref.lower():
                self.add_result(f"Bible: {ref} - {text[:90]}", ("ref", ref))
                if len(self.targets) >= 80:
                    break
        for ref, note in self.app.notes.items():
            if query in note.lower() or query in ref.lower():
                self.add_result(f"Note: {ref} - {note[:90]}", ("ref", ref))
        for entry in self.app.journal_entries:
            haystack = " ".join(str(entry.get(key, "")) for key in ("reference", "reflection", "prayer")).lower()
            if query in haystack:
                self.add_result(f"Journal: {entry.get('reference', '')} - {entry.get('reflection', '')[:90]}", ("ref", entry.get("reference", "")))
        for name, person in PEOPLE.items():
            if query in name.lower() or query in person.get("summary", "").lower():
                self.add_result(f"Person: {name} - {person.get('summary', '')[:90]}", ("person", name))
        for item in MAPS:
            if query in searchable_map_text(item).lower():
                self.add_result(f"Map: {item.get('title', '')}", ("map", item))
        for doc in self.app.library_documents:
            if query in doc.get("title", "").lower() or query in doc.get("text", "").lower():
                self.add_result(f"Document: {doc.get('title', '')}", ("document", doc))
        for ref, hymns in self.app.hymn_links.items():
            for hymn in hymns:
                if query in hymn.get("title", "").lower():
                    self.add_result(f"Hymn Link: {hymn.get('title', '')} -> {ref}", ("ref", ref))
        for hymn in self.app.hymn_favorites + self.app.recent_hymns:
            if query in hymn.get("title", "").lower():
                self.add_result(f"Hymn: {hymn.get('title', '')} ({hymn.get('hymnal', '')})", None)
        for entry in read_hymnal_index_cache().values():
            if not isinstance(entry, dict):
                continue
            hymnal_name = Path(entry.get("metadata", {}).get("path", "")).name
            for hymn in entry.get("hymns", [])[:400]:
                if query in str(hymn.get("title", "")).lower():
                    self.add_result(f"Hymnal Index: {hymn.get('title', '')} ({hymnal_name})", None)
        if not self.targets:
            self.add_result("No matches found.")

    def open_selected(self, _event=None):
        if not self.results.curselection():
            return
        target = self.targets[self.results.curselection()[0]]
        if not target:
            return
        kind, value = target
        if kind == "ref":
            self.app.open_reference(value)
        elif kind == "person":
            self.app.open_person_profile(value)
        elif kind == "map":
            MapViewerWindow(self.app, value)
        elif kind == "document":
            DocumentViewerWindow(self.app, value)


from bible_app.ui.windows.search_everything import SearchEverythingWindow  # noqa: E402


class StudyBinderWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Study Session Binder")
        self.geometry("900x700")
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Session Binder", style="Title.TLabel").pack(anchor="w")
        self.session_var = tk.StringVar()
        self.session_combo = ttk.Combobox(root, textvariable=self.session_var, state="readonly", values=[s.get("name", "") for s in self.app.study_sessions])
        self.session_combo.pack(fill="x", pady=(10, 8))
        self.session_combo.bind("<<ComboboxSelected>>", self.refresh)
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        self.views = {}
        for name in ("Passages", "Notes", "People", "Maps", "Hymns", "Documents", "Export"):
            frame = ttk.Frame(self.tabs, padding=8)
            self.tabs.add(frame, text=name)
            text = tk.Text(frame, wrap="word")
            text.pack(fill="both", expand=True)
            self.views[name] = text
        ttk.Button(root, text="Export Binder Markdown", command=self.export_binder).pack(fill="x", pady=(8, 0))
        if self.app.study_sessions:
            self.session_var.set(self.app.study_sessions[0].get("name", ""))
            self.refresh()

    def session(self):
        for session in self.app.study_sessions:
            if session.get("name") == self.session_var.get():
                return session
        return self.app.study_sessions[0] if self.app.study_sessions else None

    def set_view(self, name, text):
        widget = self.views[name]
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def refresh(self, _event=None):
        session = self.session()
        if not session:
            for name in self.views:
                self.set_view(name, "No study sessions yet.")
            return
        refs = session.get("references", [])
        self.set_view("Passages", "\n\n".join(f"{ref}\n{self.app.passage_text(ref)}" for ref in refs) or "No passages yet.")
        self.set_view("Notes", session.get("notes", "") or "No session notes yet.")
        people = sorted({person for ref in refs for person in self.app.people_for_reference(ref)})
        self.set_view("People", "\n".join(people) or "No people gathered yet.")
        maps = sorted({item.get("title", "") for ref in refs for item in maps_for_reference(ref)})
        self.set_view("Maps", "\n".join(maps) or "No maps gathered yet.")
        hymns = session.get("hymns", [])
        self.set_view("Hymns", "\n".join(f"{h.get('number', '')} {h.get('title', '')} ({h.get('hymnal', '')})" for h in hymns) or "No hymns added yet.")
        docs = session.get("documents", [])
        self.set_view("Documents", "\n".join(docs) or "No documents attached yet.")
        self.set_view("Export", "Use the export button below to save this binder as Markdown.")

    def export_binder(self):
        session = self.session()
        if not session:
            return
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", session.get("name", "binder")).strip("-")
        path = EXPORT_DIR / f"study-binder-{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [f"# {session.get('name', 'Study Binder')}", "", "## Passages", ""]
        for ref in session.get("references", []):
            lines.extend([f"### {ref}", self.app.passage_text(ref), ""])
        lines.extend(["## Notes", session.get("notes", ""), "", "## Hymns", ""])
        for hymn in session.get("hymns", []):
            lines.append(f"- {hymn.get('number', '')} {hymn.get('title', '')} ({hymn.get('hymnal', '')})")
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Study Binder", f"Exported:\n{path}")


class PresentationWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(f"Presentation - {app.selected_ref}")
        self.geometry("1000x720")
        self.configure(bg="#111111")
        title = tk.Label(self, text=app.selected_ref, bg="#111111", fg="white", font=("Segoe UI", 26, "bold"))
        title.pack(anchor="w", padx=24, pady=(20, 8))
        body = tk.Text(self, wrap="word", bg="#111111", fg="white", insertbackground="white", relief="flat", font=("Georgia", 20), padx=24, pady=16)
        body.pack(fill="both", expand=True)
        lines = [app.passage_text(app.selected_ref), ""]
        note = app.notes.get(app.selected_ref, "")
        if note:
            lines.extend(["Notes:", note, ""])
        hymns = app.hymn_links.get(app.selected_ref, [])
        if hymns:
            lines.append("Related Hymns:")
            lines.extend(f"- {h.get('number', '')} {h.get('title', '')}" for h in hymns)
        body.insert("1.0", "\n".join(lines))
        body.configure(state="disabled")
        self.bind("<Escape>", lambda _event: self.destroy())


from bible_app.ui.windows.presentation import PresentationWindow  # noqa: E402


class MapViewerWindow(tk.Toplevel):
    def __init__(self, app, map_item):
        super().__init__(app)
        self.app = app
        self.map_item = map_item
        self.image_ref = None
        self.original_image_path = resolve_local_map_image(self.map_item.get("local_image", ""))
        self.title(f"Map - {map_item.get('title', 'Map')}")
        self.geometry("980x760")
        self.minsize(720, 520)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=self.map_item.get("title", "Map"), style="Title.TLabel").pack(anchor="w")
        meta = " | ".join(
            value for value in [
                self.map_item.get("period", ""),
                self.map_item.get("region", ""),
                self.map_item.get("license", ""),
            ]
            if value
        )
        if meta:
            ttk.Label(root, text=meta, style="Muted.TLabel", wraplength=920).pack(anchor="w", pady=(4, 8))
        if self.map_item.get("summary"):
            ttk.Label(root, text=self.map_item.get("summary"), style="Muted.TLabel", wraplength=920).pack(anchor="w", pady=(0, 8))
        ttk.Button(root, text="Open Image Externally", command=self.open_external).pack(anchor="w", pady=(0, 8))

        image_path = self.original_image_path
        if not image_path or not Path(image_path).exists():
            ttk.Label(root, text="No local image is available for this map entry.", style="Muted.TLabel").pack(anchor="w")
            return

        canvas_frame = ttk.Frame(root)
        canvas_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        try:
            image = self.load_display_image(image_path)
            self.image_ref = image
            canvas.create_image(0, 0, anchor="nw", image=self.image_ref)
            canvas.configure(scrollregion=(0, 0, image.width(), image.height()))
        except Exception as exc:
            canvas.create_text(
                20,
                20,
                anchor="nw",
                text=f"Could not display the map image inside the app.\n\n{exc}\n\nUse Open Image Externally.",
                fill="#333333",
                width=700,
            )

    def load_display_image(self, image_path):
        max_width = 920
        max_height = 620
        try:
            from PIL import Image, ImageTk

            source = Image.open(image_path)
            source.thumbnail((max_width, max_height))
            return ImageTk.PhotoImage(source)
        except Exception:
            image = tk.PhotoImage(file=image_path)
            factor = max(1, int(max(image.width() / max_width, image.height() / max_height)))
            if factor > 1:
                image = image.subsample(factor, factor)
            return image

    def open_external(self):
        if not self.original_image_path or not Path(self.original_image_path).exists():
            messagebox.showinfo("Map", "No local image is available for this map entry.")
            return
        try:
            os.startfile(self.original_image_path)
        except Exception as exc:
            messagebox.showerror("Open Map", f"Could not open image:\n{exc}")


from bible_app.ui.windows.map_viewer import MapViewerWindow  # noqa: E402


class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Setup")
        self.geometry("520x750")
        self.minsize(480, 700)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Reader Setup", style="Title.TLabel").pack(anchor="w", pady=(0, 12))

        ttk.Button(root, text="Change Background Color", command=lambda: self.pick_color("reader_bg")).pack(fill="x", pady=(0, 8))
        ttk.Button(root, text="Change Text Color", command=lambda: self.pick_color("reader_fg")).pack(fill="x", pady=(0, 8))
        ttk.Button(root, text="Pick Highlighter Color", command=lambda: self.pick_color("highlight_bg")).pack(fill="x", pady=(0, 12))

        # Dark/Light mode presets
        mode_frame = ttk.Frame(root)
        mode_frame.pack(fill="x", pady=(0, 12))
        ttk.Button(mode_frame, text="Dark Mode", command=self.app.apply_dark_mode).pack(side="left", fill="x", expand=True)
        ttk.Button(mode_frame, text="Light Mode", command=self.app.apply_light_mode).pack(side="left", fill="x", expand=True, padx=(8, 0))

        ttk.Label(root, text="Highlighting Instructions", style="Section.TLabel").pack(anchor="w", pady=(8, 4))
        highlight_text = tk.Text(root, height=4, wrap="word", relief="solid", borderwidth=1)
        highlight_text.pack(fill="x", pady=(0, 12))
        highlight_text.insert("1.0", "1. Select text in the reader\n2. Press Ctrl+H or right-click Highlight\n3. Press Ctrl+U or right-click Remove Highlight\n4. Changes apply immediately")
        highlight_text.configure(state="disabled")

        ttk.Label(root, text="Keyboard Shortcuts", style="Section.TLabel").pack(anchor="w", pady=(8, 4))
        shortcuts_text = tk.Text(root, height=8, wrap="word", relief="solid", borderwidth=1)
        shortcuts_text.pack(fill="x", pady=(0, 12))
        shortcuts = """Ctrl+F - Search    |    Ctrl+B - Bookmark    |    Ctrl+N - Journal
Ctrl+T - Tags      |    Ctrl+W - Word Study  |    Ctrl+D - Settings
Ctrl+H - Highlight |    Ctrl+U - Unhighlight |    Ctrl+, - Dark Mode
Ctrl+. - Light Mode|    Alt+← Back          |    Alt+→ Forward
F5 - Refresh"""
        shortcuts_text.insert("1.0", shortcuts)
        shortcuts_text.configure(state="disabled")

        ttk.Label(root, text="Font", style="Section.TLabel").pack(anchor="w")
        self.font_var = tk.StringVar(value=self.app.settings.get("reader_font", "Georgia"))
        font_names = sorted(set(tkfont.families()))
        self.font_combo = ttk.Combobox(root, textvariable=self.font_var, values=font_names, state="readonly")
        self.font_combo.pack(fill="x", pady=(4, 10))

        ttk.Label(root, text="Font Size", style="Section.TLabel").pack(anchor="w")
        self.size_var = tk.IntVar(value=int(self.app.settings.get("reader_font_size", 13)))
        size_row = ttk.Frame(root)
        size_row.pack(fill="x", pady=(4, 12))
        ttk.Spinbox(size_row, from_=9, to=28, textvariable=self.size_var, width=8).pack(side="left")
        ttk.Button(size_row, text="Apply Font", command=self.apply_font).pack(side="left", padx=(8, 0))

        ttk.Button(root, text="Close", command=self.destroy, style="Primary.TButton").pack(fill="x", pady=(8, 0))

    def pick_color(self, key):
        current = self.app.settings.get(key, "#ffffff")
        _rgb, color = colorchooser.askcolor(initialcolor=current, parent=self)
        if not color:
            return
        self.app.settings[key] = color
        self.app.save_settings()

    def apply_font(self):
        self.app.settings["reader_font"] = self.font_var.get() or "Georgia"
        self.app.settings["reader_font_size"] = int(self.size_var.get())
        self.app.save_settings()


from bible_app.ui.windows.settings import SettingsWindow  # noqa: E402
from bible_app.ui.windows.help import HelpWindow  # noqa: E402


class PeopleReferenceWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("People Reference")
        self.geometry("860x680")
        self.minsize(720, 540)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="People Reference", style="Title.TLabel").pack(anchor="w")
        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True, pady=(10, 0))

        people_tab = ttk.Frame(tabs, padding=10)
        family_tab = ttk.Frame(tabs, padding=10)
        kings_tab = ttk.Frame(tabs, padding=10)
        prophets_tab = ttk.Frame(tabs, padding=10)
        apostles_tab = ttk.Frame(tabs, padding=10)

        tabs.add(people_tab, text="People")
        tabs.add(family_tab, text="Family Trees")
        tabs.add(kings_tab, text="Kings Timeline")
        tabs.add(prophets_tab, text="Prophets Timeline")
        tabs.add(apostles_tab, text="Apostles")

        self.build_people_tab(people_tab)
        self.build_group_tab(family_tab, PEOPLE_REFERENCE.get("family_trees", []), "people")
        self.build_group_tab(kings_tab, PEOPLE_REFERENCE.get("kings_timeline", []), "name")
        self.build_group_tab(prophets_tab, PEOPLE_REFERENCE.get("prophets_timeline", []), "name")
        self.build_group_tab(apostles_tab, PEOPLE_REFERENCE.get("apostles", []), "name")

    def build_people_tab(self, parent):
        search_row = ttk.Frame(parent)
        search_row.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_row, textvariable=self.search_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry.bind("<KeyRelease>", lambda _event: self.render_people_list())
        ttk.Button(search_row, text="Find", command=self.render_people_list).pack(side="left")

        self.people_list = tk.Listbox(parent, exportselection=False)
        self.people_list.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.people_list.bind("<<ListboxSelect>>", self.on_person_selected)

        details = ttk.Frame(parent)
        details.pack(side="left", fill="both", expand=True)
        self.person_summary = tk.Text(details, height=12, wrap="word", relief="solid", borderwidth=1)
        self.person_summary.pack(fill="both", expand=True)
        self.person_summary.configure(state="disabled")
        ttk.Button(details, text="Open Profile", command=self.open_selected_person).pack(fill="x", pady=(8, 0))

        self.visible_people = []
        self.render_people_list()

    def render_people_list(self):
        query = self.search_var.get().strip().lower()
        self.visible_people = []
        self.people_list.delete(0, "end")
        for name in sorted(PEOPLE):
            entry = PEOPLE[name]
            haystack = " ".join([
                name,
                entry.get("category", ""),
                entry.get("canon", ""),
                " ".join(entry.get("roles", [])),
                " ".join(entry.get("aliases", [])),
                entry.get("summary", ""),
                entry.get("article", ""),
            ]).lower()
            if query and query not in haystack:
                continue
            self.visible_people.append(name)
            marker = " *" if entry.get("article") else ""
            self.people_list.insert("end", f"{name}{marker}")
        self.clear_person_summary()

    def clear_person_summary(self):
        self.person_summary.configure(state="normal")
        self.person_summary.delete("1.0", "end")
        self.person_summary.insert("1.0", "Select a person to see summary, roles, references, and related people.")
        self.person_summary.configure(state="disabled")

    def on_person_selected(self, _event=None):
        if not self.people_list.curselection():
            return
        index = self.people_list.curselection()[0]
        if index >= len(self.visible_people):
            return
        name = self.visible_people[index]
        person = PEOPLE.get(name, {})
        lines = [
            name,
            "",
            f"Canon: {person.get('canon', '')}",
            f"Category: {person.get('category', '')}",
            f"Roles: {', '.join(person.get('roles', []))}",
            f"Aliases: {', '.join(person.get('aliases', []))}",
            f"Imported profile: {'yes' if person.get('article') else 'no'}",
            "",
            person.get("summary", ""),
            "",
            "References:",
        ]
        lines.extend(f"- {ref}" for ref in person.get("references", []))
        lines.extend(["", "Related People:"])
        lines.extend(f"- {related}" for related in person.get("related_people", []))
        self.person_summary.configure(state="normal")
        self.person_summary.delete("1.0", "end")
        self.person_summary.insert("1.0", "\n".join(lines))
        self.person_summary.configure(state="disabled")

    def open_selected_person(self):
        if not self.people_list.curselection():
            return
        index = self.people_list.curselection()[0]
        if index < len(self.visible_people):
            PersonWindow(self.app, self.visible_people[index])

    def build_group_tab(self, parent, entries, people_key):
        left = tk.Listbox(parent, exportselection=False)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(parent)
        right.pack(side="left", fill="both", expand=True)
        detail = tk.Text(right, height=16, wrap="word", relief="solid", borderwidth=1)
        detail.pack(fill="both", expand=True)
        refs = tk.Listbox(right, height=6, exportselection=False)
        refs.pack(fill="x", pady=(8, 0))

        for item in entries:
            left.insert("end", item.get("name", "Untitled"))

        def show_item(_event=None):
            if not left.curselection():
                return
            item = entries[left.curselection()[0]]
            people = item.get("people", []) if people_key == "people" else [item.get("name", "")]
            roles = item.get("roles", [])
            lines = [
                item.get("name", "Untitled"),
                "",
                item.get("notes", ""),
                f"Period: {item.get('period', '')}",
                f"Kingdom: {item.get('kingdom', '')}",
                f"Roles: {', '.join(roles)}" if roles else "",
                "",
                "People:",
            ]
            lines.extend(f"- {person}" for person in people if person)
            detail.configure(state="normal")
            detail.delete("1.0", "end")
            detail.insert("1.0", "\n".join(line for line in lines if line is not None))
            detail.configure(state="disabled")
            refs.delete(0, "end")
            for ref in item.get("references", []):
                refs.insert("end", ref)

        def open_ref(_event=None):
            if not refs.curselection():
                return
            self.app.open_reference(refs.get(refs.curselection()[0]))

        left.bind("<<ListboxSelect>>", show_item)
        refs.bind("<<ListboxSelect>>", open_ref)
        if entries:
            left.selection_set(0)
            show_item()


class PersonWindow(tk.Toplevel):
    def __init__(self, app, name):
        super().__init__(app)
        self.app = app
        self.name = name
        self.person = PEOPLE[name]
        self.title(f"Person - {name}")
        self.geometry("760x820")
        self.minsize(620, 580)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=self.name, style="Title.TLabel").pack(anchor="w")

        meta = []
        if self.person.get("canon"):
            meta.append(self.person.get("canon"))
        if self.person.get("category"):
            meta.append(self.person.get("category"))
        if self.person.get("roles"):
            meta.append(", ".join(self.person.get("roles", [])))
        if self.person.get("aliases"):
            meta.append("Aliases: " + ", ".join(self.person.get("aliases", [])))
        ttk.Label(root, text=" | ".join(meta), style="Muted.TLabel", wraplength=570).pack(anchor="w", pady=(4, 12))

        ttk.Label(root, text="Summary", style="Section.TLabel").pack(anchor="w")
        summary = tk.Text(root, height=5, wrap="word", relief="solid", borderwidth=1)
        summary.pack(fill="x", pady=(4, 12))
        summary.insert("1.0", self.person.get("summary", "No summary has been added yet."))
        summary.configure(state="disabled")

        if self.person.get("article"):
            ttk.Label(root, text="Imported Profile", style="Section.TLabel").pack(anchor="w")
            article = tk.Text(root, height=10, wrap="word", relief="solid", borderwidth=1)
            article.pack(fill="both", expand=True, pady=(4, 12))
            article.insert("1.0", self.person.get("article", ""))
            article.configure(state="disabled")
        if self.person.get("source"):
            ttk.Label(root, text=f"Source: {self.person.get('source')}", style="Muted.TLabel", wraplength=710).pack(anchor="w", pady=(0, 12))

        ttk.Label(root, text="References", style="Section.TLabel").pack(anchor="w")
        self.reference_list = tk.Listbox(root, height=6, exportselection=False)
        self.reference_list.pack(fill="x", pady=(4, 12))
        self.references = self.person.get("references", [])
        for ref in self.references:
            preview = self.app.verse_text(ref)
            suffix = f" - {preview[:70]}" if preview else ""
            self.reference_list.insert("end", f"{ref}{suffix}")
        self.reference_list.bind("<<ListboxSelect>>", self.on_reference_selected)

        ttk.Label(root, text="Direct Mentions In Local Library", style="Section.TLabel").pack(anchor="w")
        self.mention_refs = [ref for ref, text in self.app.all_references() if self.name.lower() in text.lower()]
        self.mention_list = tk.Listbox(root, height=6, exportselection=False)
        self.mention_list.pack(fill="x", pady=(4, 12))
        for ref in self.mention_refs[:250]:
            self.mention_list.insert("end", f"{ref} - {self.app.verse_text(ref)[:70]}")
        if len(self.mention_refs) > 250:
            self.mention_list.insert("end", f"...showing first 250 of {len(self.mention_refs)} mentions")
        if not self.mention_refs:
            self.mention_list.insert("end", "No direct name mentions found in the local translation.")
        self.mention_list.bind("<<ListboxSelect>>", self.on_mention_selected)

        ttk.Label(root, text="Related Maps", style="Section.TLabel").pack(anchor="w")
        self.person_maps = maps_for_person(self.name)
        self.person_map_list = tk.Listbox(root, height=5, exportselection=False)
        self.person_map_list.pack(fill="x", pady=(4, 12))
        for item in self.person_maps[:50]:
            self.person_map_list.insert("end", item.get("title", "Untitled map"))
        if not self.person_maps:
            self.person_map_list.insert("end", "No related maps found.")
        self.person_map_list.bind("<<ListboxSelect>>", self.on_map_selected)

        ttk.Label(root, text="Related People", style="Section.TLabel").pack(anchor="w")
        self.related_list = tk.Listbox(root, height=6, exportselection=False)
        self.related_list.pack(fill="both", expand=True, pady=(4, 0))
        self.related_people = self.person.get("related_people", [])
        for related in self.related_people:
            marker = "" if related in PEOPLE else " (not added yet)"
            self.related_list.insert("end", f"{related}{marker}")
        self.related_list.bind("<<ListboxSelect>>", self.on_related_selected)

    def on_reference_selected(self, _event=None):
        if not self.reference_list.curselection():
            return
        index = self.reference_list.curselection()[0]
        if index < len(self.references):
            self.app.open_reference(self.references[index])

    def on_mention_selected(self, _event=None):
        if not self.mention_list.curselection():
            return
        index = self.mention_list.curselection()[0]
        if index < len(self.mention_refs):
            self.app.open_reference(self.mention_refs[index])

    def on_map_selected(self, _event=None):
        if not self.person_map_list.curselection() or not self.person_maps:
            return
        index = self.person_map_list.curselection()[0]
        if index < len(self.person_maps):
            MapViewerWindow(self.app, self.person_maps[index])

    def on_related_selected(self, _event=None):
        if not self.related_list.curselection():
            return
        index = self.related_list.curselection()[0]
        if index < len(self.related_people) and self.related_people[index] in PEOPLE:
            PersonWindow(self.app, self.related_people[index])


from bible_app.ui.windows.people import PeopleReferenceWindow, PersonWindow  # noqa: E402


class ConceptLibraryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = None
        self.title("Concept Study Library")
        self.geometry("960x680")
        self.minsize(760, 540)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Concept Study Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Study ideas, doctrines, historical topics, Apocrypha-related readings, and personal research trails.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(4, 10))

        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=3)

        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Button(search_row, text="New", command=self.new_concept).pack(side="left", padx=(6, 0))

        self.concept_list = tk.Listbox(left, exportselection=False)
        self.concept_list.pack(fill="both", expand=True)
        self.concept_list.bind("<<ListboxSelect>>", self.on_concept_selected)

        ttk.Label(right, text="Name", style="Section.TLabel").pack(anchor="w")
        self.name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.name_var).pack(fill="x", pady=(4, 8))

        ttk.Label(right, text="Category", style="Section.TLabel").pack(anchor="w")
        self.category_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.category_var).pack(fill="x", pady=(4, 8))

        ttk.Label(right, text="Summary", style="Section.TLabel").pack(anchor="w")
        self.summary_text = tk.Text(right, height=5, wrap="word")
        self.summary_text.pack(fill="x", pady=(4, 8))

        lower = ttk.Frame(right)
        lower.pack(fill="both", expand=True)
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(1, weight=1)

        ttk.Label(lower, text="Bible References", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(lower, text="Related Readings / Sources", style="Section.TLabel").grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.references_list = tk.Listbox(lower, height=8, exportselection=False)
        self.references_list.grid(row=1, column=0, sticky="nsew", pady=(4, 8))
        self.references_list.bind("<Double-Button-1>", self.open_selected_reference)

        self.readings_text = tk.Text(lower, height=8, wrap="word")
        self.readings_text.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(4, 8))

        ref_buttons = ttk.Frame(lower)
        ref_buttons.grid(row=2, column=0, sticky="ew")
        ttk.Button(ref_buttons, text="Add Current Passage", command=self.add_current_reference).pack(side="left", fill="x", expand=True)
        ttk.Button(ref_buttons, text="Add Typed Reference", command=self.add_typed_reference).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(ref_buttons, text="Remove Reference", command=self.remove_reference).pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(right, text="My Notes", style="Section.TLabel").pack(anchor="w", pady=(8, 0))
        self.notes_text = tk.Text(right, height=5, wrap="word")
        self.notes_text.pack(fill="x", pady=(4, 8))

        buttons = ttk.Frame(right)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Save Concept", command=self.save_concept, style="Primary.TButton").pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Delete", command=self.delete_concept).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(buttons, text="Export Concept Notes", command=self.export_current_concept).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        self.visible_indices = []
        self.concept_list.delete(0, "end")
        for index, concept in enumerate(self.app.concepts):
            haystack = " ".join([
                concept.get("name", ""),
                concept.get("category", ""),
                concept.get("summary", ""),
                " ".join(concept.get("related_readings", [])),
                " ".join(concept.get("sources", [])),
            ]).lower()
            if query and query not in haystack:
                continue
            self.visible_indices.append(index)
            self.concept_list.insert("end", f"{concept.get('name', '')} - {concept.get('category', '')}")
        if self.current_index in self.visible_indices:
            visible = self.visible_indices.index(self.current_index)
            self.concept_list.selection_set(visible)

    def on_concept_selected(self, _event=None):
        if not self.concept_list.curselection():
            return
        visible_index = self.concept_list.curselection()[0]
        if visible_index >= len(self.visible_indices):
            return
        self.current_index = self.visible_indices[visible_index]
        self.load_concept(self.current_index)

    def load_concept(self, index):
        concept = self.app.concepts[index]
        self.name_var.set(concept.get("name", ""))
        self.category_var.set(concept.get("category", ""))
        self.set_edit_text(self.summary_text, concept.get("summary", ""))
        self.references_list.delete(0, "end")
        for ref in concept.get("references", []):
            preview = self.app.verse_text(ref)
            self.references_list.insert("end", f"{ref} - {preview[:70]}" if preview else ref)
        readings = list(concept.get("related_readings", []))
        sources = list(concept.get("sources", []))
        text = ""
        if readings:
            text += "Related readings:\n" + "\n".join(readings)
        if sources:
            text += ("\n\n" if text else "") + "Sources:\n" + "\n".join(sources)
        self.set_edit_text(self.readings_text, text)
        self.set_edit_text(self.notes_text, concept.get("notes", ""))

    def set_edit_text(self, widget, text):
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    def new_concept(self):
        now = datetime.now().isoformat(timespec="seconds")
        self.app.concepts.append({
            "name": "New Concept",
            "category": "Personal Study",
            "summary": "",
            "references": [],
            "related_readings": [],
            "notes": "",
            "sources": [],
            "created": now,
            "updated": now,
        })
        self.current_index = len(self.app.concepts) - 1
        write_concepts(self.app.concepts)
        self.refresh()
        self.load_concept(self.current_index)

    def current_references(self):
        refs = []
        for index in range(self.references_list.size()):
            raw = self.references_list.get(index).split(" - ", 1)[0].strip()
            if raw:
                refs.append(normalized_reference(raw))
        return refs

    def parse_readings_and_sources(self):
        readings = []
        sources = []
        target = readings
        for raw_line in self.readings_text.get("1.0", "end").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lower = line.lower().rstrip(":")
            if lower == "related readings":
                target = readings
                continue
            if lower == "sources":
                target = sources
                continue
            target.append(line.lstrip("- ").strip())
        return readings, sources

    def save_concept(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showinfo("Concept Study Library", "Give this concept a name before saving.")
            return
        if self.current_index is None:
            self.new_concept()
        readings, sources = self.parse_readings_and_sources()
        concept = self.app.concepts[self.current_index]
        concept.update({
            "name": name,
            "category": self.category_var.get().strip(),
            "summary": self.summary_text.get("1.0", "end").strip(),
            "references": self.current_references(),
            "related_readings": readings,
            "notes": self.notes_text.get("1.0", "end").strip(),
            "sources": sources,
            "updated": datetime.now().isoformat(timespec="seconds"),
        })
        write_concepts(self.app.concepts)
        self.refresh()
        self.app.library_status.set(f"Saved concept: {name}")

    def add_current_reference(self):
        if self.current_index is None:
            self.new_concept()
        ref = normalized_reference(self.app.selected_ref)
        refs = self.current_references()
        if ref not in refs:
            self.references_list.insert("end", ref)
        self.save_concept()

    def add_typed_reference(self):
        ref = simpledialog.askstring("Add Reference", "Enter a Bible reference:", parent=self)
        if not ref:
            return
        normalized = normalized_reference(ref)
        if normalized not in self.current_references():
            self.references_list.insert("end", normalized)
        self.save_concept()

    def remove_reference(self):
        if not self.references_list.curselection():
            return
        self.references_list.delete(self.references_list.curselection()[0])
        self.save_concept()

    def open_selected_reference(self, _event=None):
        if not self.references_list.curselection():
            return
        raw = self.references_list.get(self.references_list.curselection()[0]).split(" - ", 1)[0].strip()
        if raw:
            self.app.open_reference(raw)

    def delete_concept(self):
        if self.current_index is None or self.current_index >= len(self.app.concepts):
            return
        if not messagebox.askyesno("Concept Study Library", "Delete this concept?"):
            return
        self.app.concepts.pop(self.current_index)
        write_concepts(self.app.concepts)
        self.current_index = None
        self.name_var.set("")
        self.category_var.set("")
        self.set_edit_text(self.summary_text, "")
        self.set_edit_text(self.readings_text, "")
        self.set_edit_text(self.notes_text, "")
        self.references_list.delete(0, "end")
        self.refresh()

    def export_current_concept(self):
        if self.current_index is None:
            return
        self.save_concept()
        concept = self.app.concepts[self.current_index]
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^A-Za-z0-9_-]+", "-", concept.get("name", "concept")).strip("-") or "concept"
        path = EXPORT_DIR / f"concept-{name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [
            f"# {concept.get('name', '')}",
            "",
            f"Category: {concept.get('category', '')}",
            "",
            "## Summary",
            concept.get("summary", ""),
            "",
            "## References",
        ]
        for ref in concept.get("references", []):
            lines.extend([f"### {ref}", "", markdown_line(self.app.passage_text(ref)), ""])
        lines.extend(["## Related Readings", ""])
        lines.extend(f"- {item}" for item in concept.get("related_readings", []))
        lines.extend(["", "## Sources", ""])
        lines.extend(f"- {item}" for item in concept.get("sources", []))
        lines.extend(["", "## Notes", "", concept.get("notes", "")])
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Concept Study Library", f"Export saved to:\n{path}")


from bible_app.ui.windows.concepts import ConceptLibraryWindow  # noqa: E402


class LibraryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.filtered_documents = []
        self.title("Library Manager")
        self.geometry("720x620")
        self.minsize(600, 480)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Library Manager", style="Title.TLabel").pack(anchor="w")

        self.summary_var = tk.StringVar()
        ttk.Label(root, textvariable=self.summary_var, style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(4, 12))

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(buttons, text="Download Current Book", command=self.download_current_book).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Download New Testament", command=self.download_new_testament).pack(side="left", fill="x", expand=True, padx=(6, 0))
        tanakh_buttons = ttk.Frame(root)
        tanakh_buttons.pack(fill="x", pady=(0, 6))
        ttk.Button(tanakh_buttons, text="Download Old Testament / Hebrew Bible", command=self.download_tanakh).pack(side="left", fill="x", expand=True)
        ttk.Button(tanakh_buttons, text="Download Torah", command=self.download_torah).pack(side="left", fill="x", expand=True, padx=(6, 0))
        tanakh_buttons_2 = ttk.Frame(root)
        tanakh_buttons_2.pack(fill="x", pady=(0, 10))
        ttk.Button(tanakh_buttons_2, text="Download Prophets", command=self.download_prophets).pack(side="left", fill="x", expand=True)
        ttk.Button(tanakh_buttons_2, text="Download Writings", command=self.download_writings).pack(side="left", fill="x", expand=True, padx=(6, 0))
        doc_buttons = ttk.Frame(root)
        doc_buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(doc_buttons, text="Convert Document", command=self.convert_document).pack(side="left", fill="x", expand=True)
        ttk.Button(doc_buttons, text="View Selected Document", command=self.view_selected_document).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(doc_buttons, text="Open Original", command=self.open_selected_document_source).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(root, text="Clear KJV Cache", command=self.clear_cache).pack(fill="x", pady=(0, 10))

        ttk.Label(root, text="Cached Chapters", style="Section.TLabel").pack(anchor="w")
        self.chapter_list = tk.Listbox(root, height=10, exportselection=False)
        self.chapter_list.pack(fill="both", expand=True, pady=(4, 10))
        ttk.Label(root, text="Converted Documents", style="Section.TLabel").pack(anchor="w")
        document_search = ttk.Frame(root)
        document_search.pack(fill="x", pady=(4, 4))
        self.document_search_var = tk.StringVar()
        document_search_entry = ttk.Entry(document_search, textvariable=self.document_search_var)
        document_search_entry.pack(side="left", fill="x", expand=True)
        document_search_entry.bind("<Return>", lambda _event: self.refresh_documents())
        ttk.Button(document_search, text="Search", command=self.refresh_documents).pack(side="left", padx=(6, 0))
        ttk.Button(document_search, text="Clear", command=self.clear_document_search).pack(side="left", padx=(6, 0))
        self.document_list = tk.Listbox(root, height=6, exportselection=False)
        self.document_list.pack(fill="both", expand=True, pady=(4, 0))
        self.document_list.bind("<<ListboxSelect>>", lambda _event: self.view_selected_document())

    def refresh(self):
        kjv_cached = self.app.cached_chapter_count(translation="KJV")
        jps_cached = self.app.cached_chapter_count(translation="JPS1917")
        total_all = sum(BOOK_CHAPTERS.values())
        total_tanakh = sum(BOOK_CHAPTERS[book] for book in TANAKH_BOOKS)
        self.summary_var.set(
            f"KJV cached: {kjv_cached}/{total_all}. JPS 1917 Tanakh cached: {jps_cached}/{total_tanakh}. "
            f"Converted documents: {len(self.app.library_documents)}. "
            "Missing KJV/JPS chapters can still be opened online and saved as you use them."
        )
        self.chapter_list.delete(0, "end")
        for book in BOOK_ORDER:
            cached_book = self.app.cached_chapter_count(book, "KJV")
            total_book = BOOK_CHAPTERS[book]
            jps_text = ""
            if book in TANAKH_BOOKS:
                jps_cached_book = self.app.cached_chapter_count(book, "JPS1917")
                jps_text = f" | JPS1917 {jps_cached_book}/{total_book}"
            self.chapter_list.insert("end", f"{book}: KJV {cached_book}/{total_book}{jps_text}")
        self.refresh_documents()

    def refresh_documents(self):
        query = self.document_search_var.get().strip().lower() if hasattr(self, "document_search_var") else ""
        if query:
            self.filtered_documents = [
                item for item in self.app.library_documents
                if query in item.get("title", "").lower() or query in item.get("text", "").lower()
            ]
        else:
            self.filtered_documents = list(self.app.library_documents)
        self.document_list.delete(0, "end")
        for item in self.filtered_documents:
            self.document_list.insert("end", f"{item.get('title', '')} ({item.get('type', '')})")

    def clear_document_search(self):
        self.document_search_var.set("")
        self.refresh_documents()

    def download_current_book(self):
        self.app.start_chapter_batch_download([self.app.current_book], self.app.current_book)
        self.after(1500, self.refresh)

    def download_new_testament(self):
        self.app.start_chapter_batch_download(NEW_TESTAMENT_BOOKS, "New Testament", "KJV")
        self.after(1500, self.refresh)

    def download_tanakh(self):
        self.app.start_chapter_batch_download(TANAKH_BOOKS, "Old Testament / Hebrew Bible", "JPS1917")
        self.after(1500, self.refresh)

    def download_torah(self):
        self.app.start_chapter_batch_download(TORAH_BOOKS, "Torah", "JPS1917")
        self.after(1500, self.refresh)

    def download_prophets(self):
        self.app.start_chapter_batch_download(PROPHETS_BOOKS, "Prophets", "JPS1917")
        self.after(1500, self.refresh)

    def download_writings(self):
        self.app.start_chapter_batch_download(WRITINGS_BOOKS, "Writings", "JPS1917")
        self.after(1500, self.refresh)

    def clear_cache(self):
        self.app.clear_kjv_cache()
        self.refresh()

    def convert_document(self):
        DocumentConversionWindow(self.app, on_close=self.refresh)

    def view_selected_document(self):
        if not self.document_list.curselection():
            return
        index = self.document_list.curselection()[0]
        if index < len(self.filtered_documents):
            DocumentViewerWindow(self.app, self.filtered_documents[index])

    def open_selected_document_source(self):
        if not self.document_list.curselection():
            return
        index = self.document_list.curselection()[0]
        if index >= len(self.filtered_documents):
            return
        source_path = self.filtered_documents[index].get("source_path", "")
        if not source_path or not Path(source_path).exists():
            messagebox.showinfo("Open Original", "No local source file is available for this document.")
            return
        try:
            os.startfile(source_path)
        except Exception as exc:
            messagebox.showerror("Open Original", f"Could not open the source file:\n{exc}")


class DocumentConversionWindow(tk.Toplevel):
    def __init__(self, app, on_close=None):
        super().__init__(app)
        self.app = app
        self.on_close = on_close
        self.source_path = None
        self.title("Convert Document To Library")
        self.geometry("560x260")
        self.minsize(480, 240)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Convert Document To Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Supported: PDF, DOCX, TXT, Markdown, HTML. Converted text is saved as JSON; extracted images are stored in the document images folder.",
            style="Muted.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(4, 12))

        self.file_var = tk.StringVar(value="No document selected")
        ttk.Label(root, textvariable=self.file_var, style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(root)
        row.pack(fill="x", pady=(0, 10))
        ttk.Button(row, text="Choose Document", command=self.choose_document).pack(side="left")
        self.convert_button = ttk.Button(row, text="Convert", command=self.start_conversion, state="disabled", style="Primary.TButton")
        self.convert_button.pack(side="right")

        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=(4, 6))
        self.status_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w")

    def choose_document(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose Document",
            filetypes=[
                ("Readable documents", "*.pdf;*.docx;*.txt;*.md;*.html;*.htm"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Text files", "*.txt;*.md"),
                ("HTML files", "*.html;*.htm"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.source_path = path
        self.file_var.set(path)
        self.convert_button.configure(state="normal")

    def start_conversion(self):
        if not self.source_path:
            return
        title = simpledialog.askstring("Document Title", "Title for this library document:", initialvalue=Path(self.source_path).stem, parent=self)
        if not title:
            return
        self.convert_button.configure(state="disabled")
        self.status_var.set("Starting conversion...")
        threading.Thread(target=self.convert_worker, args=(self.source_path, title), daemon=True).start()

    def convert_worker(self, path, title):
        try:
            item = convert_document_to_library_item(
                path,
                title,
                progress=lambda value, message: self.after(0, lambda v=value, m=message: self.update_progress(v, m)),
            )
            self.after(0, lambda: self.finish_conversion(item))
        except Exception as exc:
            self.after(0, lambda e=exc: self.fail_conversion(e))

    def update_progress(self, value, message):
        self.progress_var.set(value)
        self.status_var.set(message)

    def finish_conversion(self, item):
        self.progress_var.set(100)
        self.status_var.set("Conversion complete.")
        self.app.document_conversion_finished(item)
        if self.on_close:
            self.on_close()
        self.convert_button.configure(state="normal")

    def fail_conversion(self, error):
        self.convert_button.configure(state="normal")
        self.status_var.set("Conversion failed.")
        messagebox.showerror("Convert Document", str(error))


class HymnalViewerWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.files = hymnal_files()
        self.filtered_hymns = []
        self.current_path = None
        self.load_token = 0
        self.loading = False
        self.sheet_zoom = 1.35
        self.sheet_photo = None
        self.selected_hymn = None
        if not hasattr(self.app, "hymnal_index_cache"):
            self.app.hymnal_index_cache = {}
        self.title("Hymnal Reader")
        self.geometry("980x720")
        self.minsize(780, 540)
        self.build_ui()
        if self.files:
            self.hymnal_var.set(self.files[0].name)
            self.after(100, self.load_selected_hymnal)
        else:
            self.status_var.set("No PDF hymnals were found in data/hymnals.")

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Hymnal Reader", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Choose a hymnal, then pick a hymn from the left menu.", style="Muted.TLabel").pack(anchor="w", pady=(4, 10))

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(0, 10))
        self.hymnal_var = tk.StringVar()
        self.hymnal_combo = ttk.Combobox(
            top,
            textvariable=self.hymnal_var,
            values=[path.name for path in self.files],
            state="readonly",
        )
        self.hymnal_combo.pack(side="left", fill="x", expand=True)
        self.hymnal_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_selected_hymnal())
        ttk.Button(top, text="Open PDF", command=self.open_current_pdf).pack(side="left", padx=(8, 0))

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Favorite", command=self.favorite_selected_hymn).pack(side="left")
        ttk.Button(actions, text="Link to Current Passage", command=self.link_selected_hymn).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Add to Session", command=self.add_selected_hymn_to_session).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Recent", command=self.show_recent_hymns).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Favorites", command=self.show_favorite_hymns).pack(side="left", padx=(6, 0))

        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=(0, 0, 10, 0))
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)

        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        search = ttk.Entry(search_row, textvariable=self.search_var)
        search.pack(side="left", fill="x", expand=True)
        search.bind("<KeyRelease>", lambda _event: self.refresh_hymn_list())
        ttk.Button(search_row, text="Clear", command=self.clear_search).pack(side="left", padx=(6, 0))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True)
        list_scroll = tk.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")
        self.hymn_list = tk.Listbox(list_frame, exportselection=False, yscrollcommand=list_scroll.set)
        self.hymn_list.pack(side="left", fill="both", expand=True)
        self.hymn_list.bind("<<ListboxSelect>>", self.on_hymn_selected)
        list_scroll.config(command=self.hymn_list.yview)

        self.status_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.status_var, style="Muted.TLabel", wraplength=260).pack(anchor="w", pady=(8, 0))

        self.title_var = tk.StringVar(value="Select a hymn")
        ttk.Label(right, textvariable=self.title_var, style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        view_buttons = ttk.Frame(right)
        view_buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(view_buttons, text="Zoom In", command=lambda: self.change_sheet_zoom(0.15)).pack(side="left")
        ttk.Button(view_buttons, text="Zoom Out", command=lambda: self.change_sheet_zoom(-0.15)).pack(side="left", padx=(6, 0))
        ttk.Button(view_buttons, text="Fit Width", command=self.fit_sheet_width).pack(side="left", padx=(6, 0))

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)
        sheet_tab = ttk.Frame(tabs, padding=4)
        text_tab = ttk.Frame(tabs, padding=4)
        tabs.add(sheet_tab, text="Sheet Music")
        tabs.add(text_tab, text="Text")

        sheet_frame = ttk.Frame(sheet_tab)
        sheet_frame.pack(fill="both", expand=True)
        sheet_y = tk.Scrollbar(sheet_frame)
        sheet_y.pack(side="right", fill="y")
        sheet_x = tk.Scrollbar(sheet_frame, orient="horizontal")
        sheet_x.pack(side="bottom", fill="x")
        self.sheet_canvas = tk.Canvas(
            sheet_frame,
            bg="#777777",
            highlightthickness=0,
            yscrollcommand=sheet_y.set,
            xscrollcommand=sheet_x.set,
        )
        self.sheet_canvas.pack(side="left", fill="both", expand=True)
        sheet_y.config(command=self.sheet_canvas.yview)
        sheet_x.config(command=self.sheet_canvas.xview)
        self.sheet_canvas.bind("<MouseWheel>", self.on_sheet_mousewheel)

        text_frame = ttk.Frame(text_tab)
        text_frame.pack(fill="both", expand=True)
        text_scroll = tk.Scrollbar(text_frame)
        text_scroll.pack(side="right", fill="y")
        self.reader = tk.Text(text_frame, wrap="word", yscrollcommand=text_scroll.set, font=("Georgia", 12), padx=12, pady=10)
        self.reader.pack(side="left", fill="both", expand=True)
        self.reader.configure(state="disabled")
        text_scroll.config(command=self.reader.yview)

    def selected_hymnal_path(self):
        name = self.hymnal_var.get()
        for path in self.files:
            if path.name == name:
                return path
        return None

    def load_selected_hymnal(self):
        path = self.selected_hymnal_path()
        if not path:
            return
        self.current_path = path
        self.load_token += 1
        token = self.load_token
        cache_key = str(path.resolve())
        self.status_var.set("Reading hymnal index...")
        self.loading = True
        self.filtered_hymns = []
        self.hymn_list.delete(0, "end")
        self.hymn_list.insert("end", "Loading hymns...")
        self.show_reader_message("Loading hymnal index. The reader will fill in when it is ready.")
        if cache_key in self.app.hymnal_index_cache:
            self.finish_hymnal_load(token, path, self.app.hymnal_index_cache[cache_key])
            return
        threading.Thread(target=self.load_hymnal_worker, args=(token, path, cache_key), daemon=True).start()

    def load_hymnal_worker(self, token, path, cache_key):
        try:
            hymns, from_cache = load_hymnal_index(path)
            self.app.hymnal_index_cache[cache_key] = hymns
            self.after(0, lambda: self.finish_hymnal_load(token, path, hymns, from_cache))
        except Exception as exc:
            self.after(0, lambda: self.fail_hymnal_load(token, exc))

    def finish_hymnal_load(self, token, path, hymns, from_cache=False):
        if token != self.load_token or path != self.current_path:
            return
        self.loading = False
        self.filtered_hymns = list(hymns)
        self.refresh_hymn_list()
        source = "saved index" if from_cache else "PDF scan"
        self.status_var.set(f"{len(hymns)} hymns available ({source}).")
        if hymns:
            self.hymn_list.selection_clear(0, "end")
            self.hymn_list.selection_set(0)
            self.hymn_list.activate(0)
            self.on_hymn_selected()
        else:
            self.show_reader_message("No individual hymn pages could be found in this PDF. You can still open the original PDF.")

    def fail_hymnal_load(self, token, error):
        if token != self.load_token:
            return
        self.loading = False
        self.filtered_hymns = []
        self.hymn_list.delete(0, "end")
        self.hymn_list.insert("end", "Could not read this hymnal.")
        self.status_var.set("Could not read hymnal.")
        self.show_reader_message(f"Could not read this hymnal.\n\n{error}")

    def refresh_hymn_list(self):
        if self.loading:
            return
        query = self.search_var.get().strip().lower()
        all_hymns = self.app.hymnal_index_cache.get(str(self.current_path.resolve()), []) if self.current_path else []
        if query:
            self.filtered_hymns = [
                hymn for hymn in all_hymns
                if query in hymn["title"].lower() or query in hymn["section"].lower() or query in str(hymn["number"])
            ]
        else:
            self.filtered_hymns = list(all_hymns)
        self.hymn_list.delete(0, "end")
        for hymn in self.filtered_hymns:
            self.hymn_list.insert("end", f'{hymn["number"]}. {hymn["title"]}')
        if not self.filtered_hymns:
            self.hymn_list.insert("end", "No hymns match that search.")
        self.status_var.set(f"{len(self.filtered_hymns)} hymns shown.")

    def clear_search(self):
        self.search_var.set("")
        self.refresh_hymn_list()

    def on_hymn_selected(self, _event=None):
        if not self.hymn_list.curselection() or not self.filtered_hymns:
            return
        index = self.hymn_list.curselection()[0]
        if index >= len(self.filtered_hymns):
            return
        hymn = self.filtered_hymns[index]
        self.selected_hymn = hymn
        self.app.remember_recent_hymn(hymn, self.current_path.name if self.current_path else "")
        self.title_var.set(f'{hymn["number"]}. {hymn["title"]} - {hymn["section"]} (page {hymn["page"]})')
        self.show_sheet_music(hymn)
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        self.reader.insert("1.0", hymn["text"])
        self.reader.configure(state="disabled")
        self.reader.yview_moveto(0)

    def show_reader_message(self, message):
        self.title_var.set("Hymnal Reader")
        self.sheet_photo = None
        self.sheet_canvas.delete("all")
        self.sheet_canvas.create_text(20, 20, text=message, anchor="nw", fill="white", width=620, font=("Segoe UI", 11))
        self.sheet_canvas.configure(scrollregion=self.sheet_canvas.bbox("all"))
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        self.reader.insert("1.0", message)
        self.reader.configure(state="disabled")
        self.reader.yview_moveto(0)

    def show_sheet_music(self, hymn):
        if not self.current_path:
            self.show_reader_message("No hymnal PDF is selected.")
            return
        try:
            from PIL import ImageTk

            image = render_pdf_page_image(self.current_path, hymn["page"], self.sheet_zoom)
            self.sheet_photo = ImageTk.PhotoImage(image)
            self.sheet_canvas.delete("all")
            self.sheet_canvas.create_image(12, 12, image=self.sheet_photo, anchor="nw")
            self.sheet_canvas.configure(scrollregion=(0, 0, image.width + 24, image.height + 24))
            self.sheet_canvas.xview_moveto(0)
            self.sheet_canvas.yview_moveto(0)
        except Exception as exc:
            self.sheet_photo = None
            self.sheet_canvas.delete("all")
            message = f"Could not render the sheet music page.\n\n{exc}\n\nUse Open PDF to view the original hymnal."
            self.sheet_canvas.create_text(20, 20, text=message, anchor="nw", fill="white", width=620, font=("Segoe UI", 11))
            self.sheet_canvas.configure(scrollregion=self.sheet_canvas.bbox("all"))

    def change_sheet_zoom(self, delta):
        self.sheet_zoom = min(2.5, max(0.65, self.sheet_zoom + delta))
        if self.selected_hymn:
            self.show_sheet_music(self.selected_hymn)

    def fit_sheet_width(self):
        if not self.selected_hymn or not self.current_path:
            return
        try:
            from PIL import ImageTk

            image = render_pdf_page_image(self.current_path, self.selected_hymn["page"], 1.0)
            width = max(300, self.sheet_canvas.winfo_width() - 36)
            self.sheet_zoom = min(2.5, max(0.65, width / max(1, image.width)))
            image = render_pdf_page_image(self.current_path, self.selected_hymn["page"], self.sheet_zoom)
            self.sheet_photo = ImageTk.PhotoImage(image)
            self.sheet_canvas.delete("all")
            self.sheet_canvas.create_image(12, 12, image=self.sheet_photo, anchor="nw")
            self.sheet_canvas.configure(scrollregion=(0, 0, image.width + 24, image.height + 24))
            self.sheet_canvas.xview_moveto(0)
            self.sheet_canvas.yview_moveto(0)
        except Exception as exc:
            self.show_reader_message(f"Could not fit the sheet music page.\n\n{exc}")

    def on_sheet_mousewheel(self, event):
        self.sheet_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def open_current_pdf(self):
        path = self.current_path or self.selected_hymnal_path()
        if not path or not path.exists():
            messagebox.showinfo("Open Hymnal", "No local hymnal PDF is available.")
            return
        try:
            os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Open Hymnal", f"Could not open the hymnal PDF:\n{exc}")

    def current_hymn_or_none(self):
        if self.selected_hymn:
            return self.selected_hymn
        if self.hymn_list.curselection() and self.filtered_hymns:
            index = self.hymn_list.curselection()[0]
            if index < len(self.filtered_hymns):
                return self.filtered_hymns[index]
        return None

    def favorite_selected_hymn(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        message = self.app.toggle_hymn_favorite(hymn, self.current_path.name if self.current_path else "")
        self.status_var.set(message)

    def link_selected_hymn(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        message = self.app.link_hymn_to_reference(self.app.selected_ref, hymn, self.current_path.name if self.current_path else "")
        self.status_var.set(message)
        self.app.render_related_hymns(self.app.selected_ref)
        if not is_range_reference(self.app.selected_ref):
            self.app.render_chapter()

    def add_selected_hymn_to_session(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        if not self.app.study_sessions:
            self.app.study_sessions.append({
                "name": "Hymn Study",
                "created": datetime.now().isoformat(timespec="seconds"),
                "references": [],
                "notes": "",
                "hymns": [],
                "documents": [],
            })
        session = self.app.study_sessions[0]
        session.setdefault("hymns", [])
        item = {
            "title": hymn.get("title", ""),
            "hymnal": self.current_path.name if self.current_path else "",
            "number": str(hymn.get("number", "")),
            "page": int(hymn.get("page", 0) or 0),
        }
        if item not in session["hymns"]:
            session["hymns"].append(item)
        write_study_sessions(self.app.study_sessions)
        self.status_var.set(f"Added hymn to session: {session.get('name', '')}")

    def show_recent_hymns(self):
        self.show_hymn_collection("Recent Hymns", self.app.recent_hymns)

    def show_favorite_hymns(self):
        self.show_hymn_collection("Favorite Hymns", self.app.hymn_favorites)

    def show_hymn_collection(self, title, items):
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("520x420")
        root = ttk.Frame(window, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=title, style="Title.TLabel").pack(anchor="w")
        listing = tk.Listbox(root, exportselection=False)
        listing.pack(fill="both", expand=True, pady=(10, 0))
        for item in items:
            number = f"{item.get('number')}. " if item.get("number") else ""
            listing.insert("end", f"{number}{item.get('title', '')} ({item.get('hymnal', '')})")
        if not items:
            listing.insert("end", "Nothing saved yet.")


from bible_app.ui.windows.hymnal_viewer import HymnalViewerWindow  # noqa: E402


class DocumentViewerWindow(tk.Toplevel):
    def __init__(self, app, document):
        super().__init__(app)
        self.app = app
        self.document = document
        self.title(f"Library Document - {document.get('title', '')}")
        self.geometry("900x700")
        self.minsize(700, 520)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=self.document.get("title", "Untitled Document"), style="Title.TLabel").pack(anchor="w")
        meta = f"Type: {self.document.get('type', '')} | Images: {len(self.document.get('images', []))} | Source: {self.document.get('source_path', '')}"
        ttk.Label(root, text=meta, style="Muted.TLabel", wraplength=840).pack(anchor="w", pady=(4, 10))
        ttk.Button(root, text="Open Original File", command=self.open_source).pack(anchor="w", pady=(0, 8))

        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True)
        text_tab = ttk.Frame(tabs, padding=8)
        images_tab = ttk.Frame(tabs, padding=8)
        tabs.add(text_tab, text="Text")
        tabs.add(images_tab, text="Images")

        text_scroll = tk.Scrollbar(text_tab)
        text_scroll.pack(side="right", fill="y")
        text = tk.Text(text_tab, wrap="word", yscrollcommand=text_scroll.set)
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.document.get("text", "") or "No text was extracted from this document.")
        text.configure(state="disabled")
        text_scroll.config(command=text.yview)

        image_list = tk.Listbox(images_tab, exportselection=False)
        image_list.pack(fill="both", expand=True)
        for path in self.document.get("images", []):
            image_list.insert("end", path)
        if not self.document.get("images"):
            image_list.insert("end", "No images were extracted.")
        ttk.Button(images_tab, text="Open Selected Image", command=lambda: self.open_selected_image(image_list)).pack(fill="x", pady=(8, 0))

    def open_selected_image(self, image_list):
        if not image_list.curselection() or not self.document.get("images"):
            return
        path = self.document["images"][image_list.curselection()[0]]
        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Open Image", f"Could not open image:\n{exc}")

    def open_source(self):
        source_path = self.document.get("source_path", "")
        if not source_path or not Path(source_path).exists():
            messagebox.showinfo("Open Original", "No local source file is available for this document.")
            return
        try:
            os.startfile(source_path)
        except Exception as exc:
            messagebox.showerror("Open Original", f"Could not open the source file:\n{exc}")


from bible_app.ui.windows.library import DocumentConversionWindow, DocumentViewerWindow, LibraryWindow  # noqa: E402


class JournalWindow(tk.Toplevel):
    def __init__(self, app, reference, verse_text):
        super().__init__(app)
        self.app = app
        self.reference = reference
        self.verse_text = verse_text
        self.image_paths = []
        self.title(f"Private Journal - {reference}")
        self.geometry("760x680")
        self.minsize(620, 520)
        self.build_ui()
        self.load_existing_entries()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Journal This: {self.reference}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=self.verse_text, style="Muted.TLabel", wraplength=710).pack(anchor="w", pady=(4, 12))

        ttk.Label(root, text="Reflection / Notes", style="Section.TLabel").pack(anchor="w")
        self.reflection_text = tk.Text(root, height=8, wrap="word")
        self.reflection_text.pack(fill="both", expand=True, pady=(4, 10))

        ttk.Label(root, text="Prayer", style="Section.TLabel").pack(anchor="w")
        self.prayer_text = tk.Text(root, height=6, wrap="word")
        self.prayer_text.pack(fill="both", expand=True, pady=(4, 10))

        image_row = ttk.Frame(root)
        image_row.pack(fill="x", pady=(0, 8))
        ttk.Button(image_row, text="Add Image Link", command=self.add_image).pack(side="left")
        ttk.Button(image_row, text="Save Journal Entry", command=self.save_entry, style="Primary.TButton").pack(side="right")
        self.image_label = ttk.Label(root, text="No images linked yet.", style="Muted.TLabel", wraplength=710)
        self.image_label.pack(anchor="w", pady=(0, 10))

        ttk.Label(root, text="Previous Journal Entries For This Passage", style="Section.TLabel").pack(anchor="w")
        self.entries_list = tk.Listbox(root, height=7, exportselection=False)
        self.entries_list.pack(fill="x", pady=(4, 0))

    def add_image(self):
        path = filedialog.askopenfilename(
            title="Link Image To Journal Entry",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.webp;*.tif;*.tiff"), ("All files", "*.*")],
        )
        if not path:
            return
        self.image_paths.append(path)
        self.image_label.configure(text="\n".join(self.image_paths))

    def load_existing_entries(self):
        self.entries_list.delete(0, "end")
        matches = [entry for entry in self.app.journal_entries if entry.get("reference") == self.reference]
        if not matches:
            self.entries_list.insert("end", "No journal entries for this passage yet.")
            return
        for entry in matches[-20:]:
            created = entry.get("created", "")
            summary = (entry.get("reflection", "") or entry.get("prayer", "")).replace("\n", " ")[:70]
            self.entries_list.insert("end", f"{created} - {summary}")

    def save_entry(self):
        reflection = self.reflection_text.get("1.0", "end").strip()
        prayer = self.prayer_text.get("1.0", "end").strip()
        if not reflection and not prayer and not self.image_paths:
            messagebox.showinfo("Private Journal", "Add a reflection, prayer, or image before saving.")
            return
        entry = {
            "created": datetime.now().isoformat(timespec="seconds"),
            "reference": self.reference,
            "verse": self.verse_text,
            "reflection": reflection,
            "prayer": prayer,
            "images": list(self.image_paths),
        }
        self.app.journal_entries.append(entry)
        write_journal(self.app.journal_entries)
        self.reflection_text.delete("1.0", "end")
        self.prayer_text.delete("1.0", "end")
        self.image_paths = []
        self.image_label.configure(text="No images linked yet.")
        self.load_existing_entries()
        messagebox.showinfo("Private Journal", "Journal entry saved.")


from bible_app.ui.windows.journal import JournalWindow  # noqa: E402


class CrossReferenceGraphWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Cross-Reference Graph")
        self.geometry("760x560")
        self.minsize(620, 420)
        self.edges = cross_reference_edges(app.selected_ref)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Cross-Reference Graph: {self.app.selected_ref}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Select a link to open the connected passage.", style="Muted.TLabel").pack(anchor="w", pady=(4, 10))
        self.link_list = tk.Listbox(root, exportselection=False)
        self.link_list.pack(fill="both", expand=True)
        self.link_list.bind("<<ListboxSelect>>", self.open_selected)
        if not self.edges:
            self.link_list.insert("end", "No cross-reference links available for this passage.")
            return
        for source, target in self.edges:
            self.link_list.insert("end", f"{source} -> {target}")

    def open_selected(self, _event=None):
        if not self.link_list.curselection() or not self.edges:
            return
        _source, target = self.edges[self.link_list.curselection()[0]]
        self.app.open_reference(target)


from bible_app.ui.windows.cross_reference import CrossReferenceGraphWindow  # noqa: E402


class StudySessionsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = None
        self.title("Study Sessions")
        self.geometry("860x620")
        self.minsize(700, 480)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Session Workspace", style="Title.TLabel").pack(anchor="w")
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, pady=(10, 0))
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        self.session_list = tk.Listbox(left, exportselection=False)
        self.session_list.pack(fill="both", expand=True)
        self.session_list.bind("<<ListboxSelect>>", self.on_session_selected)
        ttk.Button(left, text="New Session", command=self.new_session).pack(fill="x", pady=(8, 0))
        ttk.Button(left, text="Add Current Passage", command=self.add_current).pack(fill="x", pady=(6, 0))
        self.refs_list = tk.Listbox(right, height=10, exportselection=False)
        self.refs_list.pack(fill="x")
        self.refs_list.bind("<<ListboxSelect>>", self.open_ref)
        ttk.Label(right, text="Session Notes", style="Section.TLabel").pack(anchor="w", pady=(10, 4))
        self.notes_text = tk.Text(right, height=10, wrap="word")
        self.notes_text.pack(fill="both", expand=True)
        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Save", command=self.save_current).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Export", command=self.export_current).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        self.session_list.delete(0, "end")
        for session in self.app.study_sessions:
            self.session_list.insert("end", f"{session['name']} ({len(session.get('references', []))})")
        if self.app.study_sessions and self.current_index is None:
            self.session_list.selection_set(0)
            self.on_session_selected()

    def new_session(self):
        name = simpledialog.askstring("Study Session", "Session name:", parent=self)
        if not name:
            return
        self.app.study_sessions.append({"name": name.strip(), "created": datetime.now().isoformat(timespec="seconds"), "references": [], "notes": ""})
        write_study_sessions(self.app.study_sessions)
        self.current_index = len(self.app.study_sessions) - 1
        self.refresh()

    def on_session_selected(self, _event=None):
        if not self.session_list.curselection():
            return
        self.current_index = self.session_list.curselection()[0]
        session = self.app.study_sessions[self.current_index]
        self.refs_list.delete(0, "end")
        for ref in session.get("references", []):
            self.refs_list.insert("end", f"{ref} - {self.app.passage_text(ref)[:70]}")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", session.get("notes", ""))

    def add_current(self):
        if self.current_index is None:
            self.new_session()
            if self.current_index is None:
                return
        session = self.app.study_sessions[self.current_index]
        if self.app.selected_ref not in session["references"]:
            session["references"].append(self.app.selected_ref)
        write_study_sessions(self.app.study_sessions)
        self.on_session_selected()
        self.refresh()

    def save_current(self):
        if self.current_index is None:
            return
        self.app.study_sessions[self.current_index]["notes"] = self.notes_text.get("1.0", "end").strip()
        write_study_sessions(self.app.study_sessions)

    def open_ref(self, _event=None):
        if self.current_index is None or not self.refs_list.curselection():
            return
        ref = self.app.study_sessions[self.current_index]["references"][self.refs_list.curselection()[0]]
        self.app.open_reference(ref)

    def export_current(self):
        if self.current_index is None:
            return
        self.save_current()
        session = self.app.study_sessions[self.current_index]
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", session["name"]).strip("-")
        path = EXPORT_DIR / f"study-session-{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [f"# {session['name']}", "", f"Created: {session.get('created', '')}", "", "## Passages", ""]
        for ref in session.get("references", []):
            lines.extend([f"### {ref}", "", self.app.passage_text(ref), ""])
        lines.extend(["## Notes", "", session.get("notes", "")])
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Exported to:\n{path}")


class ReadingPlansWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = 0
        self.title("Reading Plans")
        self.geometry("780x580")
        self.minsize(640, 440)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Reading Plans", style="Title.TLabel").pack(anchor="w")
        self.plan_var = tk.StringVar()
        self.plan_combo = ttk.Combobox(root, textvariable=self.plan_var, state="readonly")
        self.plan_combo.pack(fill="x", pady=(10, 8))
        self.plan_combo.bind("<<ComboboxSelected>>", self.on_plan_selected)
        self.progress_var = tk.StringVar()
        ttk.Label(root, textvariable=self.progress_var, style="Muted.TLabel").pack(anchor="w")
        self.refs_list = tk.Listbox(root, exportselection=False)
        self.refs_list.pack(fill="both", expand=True, pady=(8, 8))
        self.refs_list.bind("<<ListboxSelect>>", self.open_selected)
        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Mark Complete", command=self.mark_complete).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Open Next", command=self.open_next).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        self.plan_combo.configure(values=[plan["name"] for plan in self.app.reading_plans])
        if self.app.reading_plans:
            self.plan_var.set(self.app.reading_plans[self.current_index]["name"])
        self.render_refs()

    def current_plan(self):
        if not self.app.reading_plans:
            return None
        return self.app.reading_plans[self.current_index]

    def on_plan_selected(self, _event=None):
        for index, plan in enumerate(self.app.reading_plans):
            if plan["name"] == self.plan_var.get():
                self.current_index = index
                break
        self.render_refs()

    def render_refs(self):
        self.refs_list.delete(0, "end")
        plan = self.current_plan()
        if not plan:
            return
        completed = set(plan.get("completed", []))
        total = len(plan.get("references", []))
        done = len(completed)
        self.progress_var.set(f"{done}/{total} complete")
        for ref in plan.get("references", []):
            marker = "[x]" if ref in completed else "[ ]"
            self.refs_list.insert("end", f"{marker} {ref}")

    def selected_ref(self):
        plan = self.current_plan()
        if not plan or not self.refs_list.curselection():
            return None
        return plan["references"][self.refs_list.curselection()[0]]

    def open_selected(self, _event=None):
        ref = self.selected_ref()
        if ref:
            self.app.open_reference(ref)

    def mark_complete(self):
        ref = self.selected_ref()
        plan = self.current_plan()
        if not ref or not plan:
            return
        if ref not in plan["completed"]:
            plan["completed"].append(ref)
        write_reading_plans(self.app.reading_plans)
        self.render_refs()

    def open_next(self):
        plan = self.current_plan()
        if not plan:
            return
        completed = set(plan.get("completed", []))
        for index, ref in enumerate(plan.get("references", [])):
            if ref not in completed:
                self.refs_list.selection_clear(0, "end")
                self.refs_list.selection_set(index)
                self.refs_list.see(index)
                self.app.open_reference(ref)
                return


from bible_app.ui.windows.sessions import ReadingPlansWindow, StudyBinderWindow, StudySessionsWindow  # noqa: E402


class TagWindow(tk.Toplevel):
    """Window for managing verse tags"""
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Verse Tags")
        self.geometry("600x500")
        self.minsize(500, 400)
        self.build_ui()
    
    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Organize Verses with Tags", style="Title.TLabel").pack(anchor="w")
        
        # Tag creation
        tag_frame = ttk.Frame(root)
        tag_frame.pack(fill="x", pady=(10, 10))
        ttk.Label(tag_frame, text="New Tag:").pack(side="left")
        self.tag_var = tk.StringVar()
        ttk.Entry(tag_frame, textvariable=self.tag_var, width=30).pack(side="left", padx=(5, 10))
        ttk.Button(tag_frame, text="Add Tag to Current Verse", command=self.add_tag).pack(side="left")
        
        # Tags list for current verse
        ttk.Label(root, text=f"Tags for {self.app.selected_ref}", style="Section.TLabel").pack(anchor="w", pady=(10, 4))
        self.tags_listbox = tk.Listbox(root, height=5, exportselection=False)
        self.tags_listbox.pack(fill="x", pady=(0, 10))
        ttk.Button(root, text="Remove Selected Tag", command=self.remove_tag).pack(fill="x", pady=(0, 10))
        
        # All tags
        ttk.Label(root, text="All Tags in Study", style="Section.TLabel").pack(anchor="w", pady=(10, 4))
        self.all_tags_listbox = tk.Listbox(root, height=10, exportselection=False)
        self.all_tags_listbox.pack(fill="both", expand=True, pady=(0, 10))
        self.all_tags_listbox.bind("<<ListboxSelect>>", self.on_tag_selected)
        
        self.refresh_tags()
    
    def add_tag(self):
        tag = self.tag_var.get().strip()
        if not tag:
            messagebox.showwarning("Tag", "Please enter a tag name")
            return
        self.app.add_verse_tag(self.app.selected_ref, tag)
        self.tag_var.set("")
        self.refresh_tags()
        messagebox.showinfo("Tag", f"Tag '{tag}' added to {self.app.selected_ref}")
    
    def remove_tag(self):
        if not self.tags_listbox.curselection():
            return
        tag = self.tags_listbox.get(self.tags_listbox.curselection()[0])
        self.app.remove_verse_tag(self.app.selected_ref, tag)
        self.refresh_tags()
    
    def on_tag_selected(self, event):
        if not self.all_tags_listbox.curselection():
            return
        # Could add functionality to show all verses with this tag
    
    def refresh_tags(self):
        # Current verse tags
        self.tags_listbox.delete(0, "end")
        tags = self.app.verse_tags.get(self.app.selected_ref, [])
        for tag in tags:
            self.tags_listbox.insert("end", tag)
        
        # All tags
        all_tags = set()
        for tags_list in self.app.verse_tags.values():
            all_tags.update(tags_list)
        self.all_tags_listbox.delete(0, "end")
        for tag in sorted(all_tags):
            count = sum(1 for t in self.app.verse_tags.values() if tag in t)
            self.all_tags_listbox.insert("end", f"{tag} ({count})")


class WordStudyWindow(tk.Toplevel):
    """Window for word study and frequency analysis"""
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.occurrences = []
        self.title("Word Study Tool")
        self.geometry("700x600")
        self.minsize(600, 500)
        self.build_ui()
    
    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Word Study & Frequency Analysis", style="Title.TLabel").pack(anchor="w")
        
        # Search word
        search_frame = ttk.Frame(root)
        search_frame.pack(fill="x", pady=(10, 10))
        ttk.Label(search_frame, text="Search Word:").pack(side="left")
        self.word_var = tk.StringVar()
        word_entry = ttk.Entry(search_frame, textvariable=self.word_var, width=30)
        word_entry.pack(side="left", padx=(5, 10))
        word_entry.bind("<Return>", lambda _event: self.search_word())
        ttk.Button(search_frame, text="Find Occurrences", command=self.search_word).pack(side="left")
        word_entry.focus_set()
        
        # Results
        self.summary_var = tk.StringVar(value="Search results will appear below.")
        ttk.Label(root, textvariable=self.summary_var, style="Section.TLabel").pack(anchor="w", pady=(10, 4))
        ttk.Label(
            root,
            text="Select a result to open that verse in the main reader.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        
        scrollbar = tk.Scrollbar(root)
        scrollbar.pack(side="right", fill="y")
        self.results_listbox = tk.Listbox(root, yscrollcommand=scrollbar.set, exportselection=False)
        self.results_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.results_listbox.yview)
        self.results_listbox.bind("<<ListboxSelect>>", self.on_result_selected)
    
    def search_word(self):
        word = self.word_var.get().strip()
        if not word:
            messagebox.showwarning("Search", "Please enter a word to search")
            return
        
        self.results_listbox.delete(0, "end")
        self.occurrences = word_occurrences(BIBLE.get(self.app.translation, {}), word)

        verse_count = len(self.occurrences)
        match_count = sum(item["count"] for item in self.occurrences)
        if not self.occurrences:
            self.summary_var.set(f"No matches for '{word}' in the local {self.app.translation} library.")
            self.results_listbox.insert("end", "No matches in the local library")
            return

        self.summary_var.set(
            f"Found {match_count} match{'es' if match_count != 1 else ''} "
            f"in {verse_count} verse{'s' if verse_count != 1 else ''}."
        )

        for item in self.occurrences[:500]:
            ref = item["reference"]
            text = item["text"]
            count = item["count"]
            preview = text[:95] + "..." if len(text) > 95 else text
            count_label = f"{count}x" if count > 1 else "1x"
            self.results_listbox.insert("end", f"{ref} ({count_label}) - {preview}")

        if len(self.occurrences) > 500:
            self.results_listbox.insert("end", f"...showing first 500 of {len(self.occurrences)} verses")
    
    def on_result_selected(self, event):
        if not self.results_listbox.curselection():
            return
        index = self.results_listbox.curselection()[0]
        if index >= len(self.occurrences):
            return
        self.app.open_reference(self.occurrences[index]["reference"])


class TranslationComparisonWindow(tk.Toplevel):
    """Window for comparing two to four local translations."""
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.translation_options = self.local_translation_choices()
        self.translation_vars = []
        self.text_widgets = []
        self.title("Translation Comparison")
        self.geometry("1080x680")
        self.minsize(860, 520)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Translation Comparison", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=f"Reference: {self.app.selected_ref}", style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        control_row = ttk.Frame(root)
        control_row.pack(fill="x", pady=(0, 8))
        ttk.Label(control_row, text="Columns:").pack(side="left")
        self.column_count_var = tk.IntVar(value=min(4, max(2, len(self.translation_options))))
        self.column_count = ttk.Spinbox(control_row, from_=2, to=4, textvariable=self.column_count_var, width=5, command=self.rebuild_grid)
        self.column_count.pack(side="left", padx=(6, 14))
        ttk.Button(control_row, text="Reload", command=self.rebuild_grid).pack(side="left")
        self.status_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 8))

        self.chooser_frame = ttk.Frame(root)
        self.chooser_frame.pack(fill="x", pady=(0, 8))
        self.grid_frame = ttk.Frame(root)
        self.grid_frame.pack(fill="both", expand=True)
        self.rebuild_grid()

    def local_translation_choices(self):
        choices = []
        for choice in self.app.translation_choices():
            code = self.app.translation_code_from_choice(choice)
            if code in BIBLE:
                choices.append(choice)
        return choices or [self.app.translation_choice_for(self.app.translation)]

    def rebuild_grid(self):
        for child in self.chooser_frame.winfo_children():
            child.destroy()
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.translation_vars = []
        self.text_widgets = []
        count = max(2, min(4, int(self.column_count_var.get())))

        for index in range(count):
            default = self.translation_options[index % len(self.translation_options)]
            if index == 0:
                current = self.app.translation_choice_for(self.app.translation)
                if current in self.translation_options:
                    default = current
            var = tk.StringVar(value=default)
            self.translation_vars.append(var)
            ttk.Label(self.chooser_frame, text=f"{index + 1}:").pack(side="left")
            combo = ttk.Combobox(self.chooser_frame, textvariable=var, values=self.translation_options, state="readonly", width=26)
            combo.pack(side="left", fill="x", expand=True, padx=(4, 8))
            combo.bind("<<ComboboxSelected>>", lambda _event: self.load_comparison())

            self.grid_frame.grid_columnconfigure(index, weight=1)
            label = ttk.Label(self.grid_frame, text="", style="Section.TLabel")
            label.grid(row=0, column=index, sticky="w", padx=5)
            text = tk.Text(self.grid_frame, wrap="word", height=18)
            text.grid(row=1, column=index, sticky="nsew", padx=5, pady=(4, 0))
            text.tag_configure("diff", background="#fff4c2")
            text.configure(state="disabled")
            self.text_widgets.append((label, text))
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.load_comparison()

    def set_text(self, widget, text, diff_words=None):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        if diff_words:
            for word in sorted(diff_words, key=len, reverse=True):
                start = "1.0"
                while True:
                    pos = widget.search(word, start, nocase=True, stopindex="end")
                    if not pos:
                        break
                    end = f"{pos}+{len(word)}c"
                    widget.tag_add("diff", pos, end)
                    start = end
        widget.configure(state="disabled")

    def load_comparison(self):
        ref = self.app.selected_ref
        selected = [self.app.translation_code_from_choice(var.get()) for var in self.translation_vars]
        texts = [verse_text_from_translation(code, ref) for code in selected]
        common_words = None
        word_sets = []
        for text in texts:
            words = {word.lower() for word in re.findall(r"\b[A-Za-z]{4,}\b", text)}
            word_sets.append(words)
            common_words = words if common_words is None else common_words.intersection(words)
        common_words = common_words or set()
        for index, (label, widget) in enumerate(self.text_widgets):
            code = selected[index]
            text = texts[index] or f"{ref} is not available in {code}."
            diff_words = word_sets[index] - common_words if texts[index] else set()
            label.configure(text=code)
            self.set_text(widget, text, diff_words=diff_words)
        self.status_var.set("Highlighted words are less shared across the selected translations.")


if __name__ == "__main__":
    BibleReferenceApp().mainloop()
