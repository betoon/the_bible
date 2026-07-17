# Bible App Refactoring - Code Examples

This document provides concrete code examples for the highest-impact refactoring tasks.

---

## 1. CONFIG & CONSTANTS EXTRACTION

### config/constants.py
```python
"""Bible book names, chapters, and static data."""

BOOK_CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    # ... rest of books
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
    "Ecclesiastes", "Esther", "Daniel", "Ezra", "Nehemiah", "1 Chronicles", "2 Chronicles",
]

TRANSLATION_LABELS = {
    "KJV": "King James Version",
    "JPS1917": "JPS 1917 Hebrew Bible / Tanakh",
    "NIV": "New International Version",
    "ESV": "English Standard Version",
}

# UI Colors
UI_COLORS = {
    "bg_main": "#F3F3F3",
    "bg_panel": "#FFFFFF",
    "accent": "#0066cc",
    "text_primary": "#000000",
    "text_muted": "#666666",
    "error": "#dc3545",
    "success": "#28a745",
}

# API Configuration
BIBLE_API_URL = "https://bible-api.com/{reference}?translation={translation}"
JPS_BASE_URL = "https://www.mechon-mamre.org/e/et/{code}{chapter:02d}.htm"

# Regular expressions
import re
STRONGS_PATTERN = re.compile(r"\{[HG]\d+[a-zA-Z]*\}|\{\([HG]?\d+[a-zA-Z]*\)\}")
BIBLE_REFERENCE_PATTERN = re.compile(
    r"^([\d]+\s+)?([A-Za-z\s]+)\s+(\d+):(\d+)(?:-(\d+))?$"
)
```

### config/settings.py
```python
"""Application settings and configuration."""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Centralized application settings."""
    
    # Directories
    @staticmethod
    def get_app_data_dir() -> Path:
        """Get platform-appropriate app data directory."""
        if os.name == 'nt':  # Windows
            root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:  # macOS, Linux
            root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return root / "BibleReferenceApp"
    
    # Instance-level settings
    def __init__(self):
        self.app_dir = self.get_app_data_dir()
        self.user_data_dir = self.app_dir / "user_data"
        self.cache_dir = self.app_dir / "cache"
        self.logs_dir = self.app_dir / "logs"
        self.backups_dir = self.app_dir / "backups"
        
        # Create directories
        for directory in [self.user_data_dir, self.cache_dir, self.logs_dir, self.backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.notes_file = self.user_data_dir / "notes.json"
        self.journal_file = self.user_data_dir / "journal.json"
        self.bookmarks_file = self.user_data_dir / "bookmarks.json"
        self.highlights_file = self.user_data_dir / "highlights.json"
        self.settings_file = self.user_data_dir / "settings.json"
        
        # API settings
        self.api_timeout = 10
        self.api_retries = 3
        self.cache_ttl = 86400  # 24 hours
        
        # UI settings
        self.window_width = 1200
        self.window_height = 800
        self.font_size = 12
        self.theme = "light"
        
    def to_dict(self) -> dict:
        """Convert settings to dictionary for JSON storage."""
        return {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "font_size": self.font_size,
            "theme": self.theme,
        }
    
    def from_dict(self, data: dict) -> None:
        """Load settings from dictionary."""
        self.window_width = data.get("window_width", self.window_width)
        self.window_height = data.get("window_height", self.window_height)
        self.font_size = data.get("font_size", self.font_size)
        self.theme = data.get("theme", self.theme)

# Global settings instance
settings = Settings()
```

---

## 2. LOGGING SETUP

### utils/logger.py
```python
"""Logging configuration and utilities."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

class LoggerSetup:
    """Configure application logging."""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = __name__) -> logging.Logger:
        """Get configured logger instance."""
        if cls._instance is None:
            cls._instance = cls._setup()
        return logging.getLogger(name)
    
    @staticmethod
    def _setup() -> logging.Logger:
        """Configure logging with file and console handlers."""
        from config.settings import settings
        
        # Create logger
        logger = logging.getLogger("bible_app")
        logger.setLevel(logging.DEBUG)
        
        # File handler - rotate every day, keep 7 days
        log_file = settings.logs_dir / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=7
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (for development)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info("Logger initialized")
        return logger

# Convenience function
def get_logger(name: str = __name__) -> logging.Logger:
    """Get application logger."""
    return LoggerSetup.get_logger(name)
```

---

## 3. DATA MODELS

### storage/models.py
```python
"""Data models for application entities."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

@dataclass
class BibleNote:
    """A note attached to a Bible verse."""
    reference: str
    text: str
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate note data."""
        if not self.reference or not self.reference.strip():
            raise ValidationError("Reference is required")
        if not self.text or not self.text.strip():
            raise ValidationError("Text is required")
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BibleNote':
        """Create from dictionary."""
        obj = cls(**data)
        obj.validate()
        return obj

@dataclass
class Bookmark:
    """A bookmarked Bible passage."""
    reference: str
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    label: Optional[str] = None
    
    def validate(self) -> bool:
        if not self.reference or not self.reference.strip():
            raise ValidationError("Reference is required")
        return True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bookmark':
        obj = cls(**data)
        obj.validate()
        return obj

@dataclass
class Highlight:
    """A highlighted Bible verse."""
    reference: str
    text: str
    color: str  # e.g., "#ffff00"
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def validate(self) -> bool:
        if not self.reference:
            raise ValidationError("Reference is required")
        if not self.text:
            raise ValidationError("Text is required")
        if not self.color.startswith("#"):
            raise ValidationError("Color must be hex format")
        return True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Highlight':
        obj = cls(**data)
        obj.validate()
        return obj

@dataclass
class JournalEntry:
    """A journal entry for a Bible passage."""
    reference: str
    verse_text: str
    reflection: str = ""
    prayer: str = ""
    images: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def validate(self) -> bool:
        if not self.reference:
            raise ValidationError("Reference is required")
        if not self.reflection and not self.prayer and not self.images:
            raise ValidationError("Add a reflection, prayer, or image")
        return True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'JournalEntry':
        obj = cls(**data)
        obj.validate()
        return obj
```

---

## 4. DATA PERSISTENCE

### storage/data_manager.py
```python
"""Manage persistent data storage."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from storage.models import BibleNote, Bookmark, Highlight, JournalEntry, ValidationError

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Raised when data loading fails."""
    pass

class DataManager:
    """Manage application data persistence."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / "notes.json"
        self.bookmarks_file = self.data_dir / "bookmarks.json"
        self.highlights_file = self.data_dir / "highlights.json"
        self.journal_file = self.data_dir / "journal.json"
    
    # NOTES
    def load_notes(self) -> List[BibleNote]:
        """Load all notes from disk."""
        if not self.notes_file.exists():
            return []
        try:
            data = json.loads(self.notes_file.read_text())
            return [BibleNote.from_dict(n) for n in data]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to load notes: {e}")
            raise DataLoadError(f"Corrupted notes file: {e}")
        except ValidationError as e:
            logger.error(f"Invalid note data: {e}")
            raise DataLoadError(f"Invalid note format: {e}")
    
    def save_notes(self, notes: List[BibleNote]) -> None:
        """Save all notes to disk."""
        try:
            data = [n.to_dict() for n in notes]
            self.notes_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(notes)} notes")
        except Exception as e:
            logger.error(f"Failed to save notes: {e}")
            raise
    
    # BOOKMARKS
    def load_bookmarks(self) -> List[Bookmark]:
        """Load all bookmarks from disk."""
        if not self.bookmarks_file.exists():
            return []
        try:
            data = json.loads(self.bookmarks_file.read_text())
            return [Bookmark.from_dict(b) for b in data]
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to load bookmarks: {e}")
            raise DataLoadError(f"Invalid bookmarks file: {e}")
    
    def save_bookmarks(self, bookmarks: List[Bookmark]) -> None:
        """Save all bookmarks to disk."""
        try:
            data = [b.to_dict() for b in bookmarks]
            self.bookmarks_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(bookmarks)} bookmarks")
        except Exception as e:
            logger.error(f"Failed to save bookmarks: {e}")
            raise
    
    # HIGHLIGHTS
    def load_highlights(self) -> List[Highlight]:
        """Load all highlights from disk."""
        if not self.highlights_file.exists():
            return []
        try:
            data = json.loads(self.highlights_file.read_text())
            return [Highlight.from_dict(h) for h in data]
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to load highlights: {e}")
            raise DataLoadError(f"Invalid highlights file: {e}")
    
    def save_highlights(self, highlights: List[Highlight]) -> None:
        """Save all highlights to disk."""
        try:
            data = [h.to_dict() for h in highlights]
            self.highlights_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(highlights)} highlights")
        except Exception as e:
            logger.error(f"Failed to save highlights: {e}")
            raise
    
    # JOURNAL
    def load_journal(self) -> List[JournalEntry]:
        """Load all journal entries from disk."""
        if not self.journal_file.exists():
            return []
        try:
            data = json.loads(self.journal_file.read_text())
            return [JournalEntry.from_dict(j) for j in data]
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to load journal: {e}")
            raise DataLoadError(f"Invalid journal file: {e}")
    
    def save_journal(self, entries: List[JournalEntry]) -> None:
        """Save all journal entries to disk."""
        try:
            data = [e.to_dict() for e in entries]
            self.journal_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Saved {len(entries)} journal entries")
        except Exception as e:
            logger.error(f"Failed to save journal: {e}")
            raise
    
    def search_notes(self, query: str) -> List[BibleNote]:
        """Search notes by text content."""
        notes = self.load_notes()
        query_lower = query.lower()
        return [n for n in notes if query_lower in n.text.lower() or query_lower in n.reference.lower()]
    
    def get_notes_for_reference(self, reference: str) -> List[BibleNote]:
        """Get all notes for a specific Bible reference."""
        notes = self.load_notes()
        return [n for n in notes if n.reference == reference]
```

---

## 5. VALIDATION UTILITIES

### utils/validators.py
```python
"""Input validation utilities."""

import re
from typing import Tuple, Optional
from config.constants import BOOK_CHAPTERS, BOOK_ORDER

class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class BibleReferenceValidator:
    """Validate Bible reference formats."""
    
    # Pattern: "Book Chapter:Verse" or "Chapter:Verse-EndVerse"
    PATTERN = re.compile(
        r'^([\d]+\s+)?([A-Za-z\s]+)\s+(\d+):(\d+)(?:-(\d+))?$'
    )
    
    @staticmethod
    def validate(reference: str) -> bool:
        """
        Validate Bible reference format.
        
        Valid formats:
        - Genesis 1:1
        - Psalm 23
        - 1 Samuel 2:11
        - John 3:16-17
        
        Args:
            reference: Bible reference string
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If invalid format or non-existent book
        """
        reference = reference.strip()
        match = BibleReferenceValidator.PATTERN.match(reference)
        
        if not match:
            raise ValidationError(f"Invalid reference format: {reference}")
        
        book = match.group(2).strip()
        chapter = int(match.group(3))
        verse_start = int(match.group(4))
        verse_end = int(match.group(5)) if match.group(5) else verse_start
        
        # Check book exists
        if book not in BOOK_CHAPTERS:
            raise ValidationError(f"Unknown book: {book}")
        
        # Check chapter is valid
        max_chapters = BOOK_CHAPTERS[book]
        if chapter < 1 or chapter > max_chapters:
            raise ValidationError(
                f"{book} has only {max_chapters} chapters, not {chapter}"
            )
        
        # Check verses are in order
        if verse_end < verse_start:
            raise ValidationError(f"Invalid verse range: {verse_start}-{verse_end}")
        
        return True
    
    @staticmethod
    def parse(reference: str) -> Tuple[str, int, int, Optional[int]]:
        """
        Parse Bible reference into components.
        
        Returns:
            (book, chapter, verse_start, verse_end)
        """
        BibleReferenceValidator.validate(reference)
        match = BibleReferenceValidator.PATTERN.match(reference.strip())
        
        book = match.group(2).strip()
        chapter = int(match.group(3))
        verse_start = int(match.group(4))
        verse_end = int(match.group(5)) if match.group(5) else None
        
        return (book, chapter, verse_start, verse_end)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_hex_color(color: str) -> bool:
    """Validate hex color format."""
    pattern = r'^#[0-9a-fA-F]{6}$'
    return re.match(pattern, color) is not None

def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Sanitize user input text."""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text
```

---

## 6. SIMPLE TESTING EXAMPLE

### tests/test_validators.py
```python
"""Tests for validation utilities."""

import pytest
from utils.validators import BibleReferenceValidator, ValidationError

class TestBibleReferenceValidator:
    """Test Bible reference validation."""
    
    def test_valid_single_verse(self):
        """Test valid single verse reference."""
        assert BibleReferenceValidator.validate("Genesis 1:1")
        assert BibleReferenceValidator.validate("John 3:16")
        assert BibleReferenceValidator.validate("Psalm 23:1")
    
    def test_valid_verse_range(self):
        """Test valid verse range reference."""
        assert BibleReferenceValidator.validate("John 3:16-17")
        assert BibleReferenceValidator.validate("Genesis 1:1-5")
    
    def test_valid_multi_word_book(self):
        """Test books with multiple words."""
        assert BibleReferenceValidator.validate("1 Samuel 2:11")
        assert BibleReferenceValidator.validate("Song of Solomon 1:1")
    
    def test_invalid_format(self):
        """Test invalid reference formats."""
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("John3:16")  # Missing space
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("John 3-16")  # Wrong separator
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("")  # Empty
    
    def test_invalid_book(self):
        """Test non-existent books."""
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("Fake Book 1:1")
    
    def test_chapter_out_of_range(self):
        """Test invalid chapter numbers."""
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("Genesis 51:1")  # Too many chapters
        with pytest.raises(ValidationError):
            BibleReferenceValidator.validate("Obadiah 2:1")  # Only 1 chapter
    
    def test_parse_single_verse(self):
        """Test parsing reference."""
        book, chapter, start, end = BibleReferenceValidator.parse("John 3:16")
        assert book == "John"
        assert chapter == 3
        assert start == 16
        assert end is None
    
    def test_parse_verse_range(self):
        """Test parsing verse range."""
        book, chapter, start, end = BibleReferenceValidator.parse("John 3:16-17")
        assert book == "John"
        assert chapter == 3
        assert start == 16
        assert end == 17
```

### tests/test_models.py
```python
"""Tests for data models."""

import pytest
from storage.models import BibleNote, ValidationError

class TestBibleNote:
    """Test BibleNote model."""
    
    def test_create_valid_note(self):
        """Test creating a valid note."""
        note = BibleNote(
            reference="John 3:16",
            text="Test note"
        )
        assert note.validate()
    
    def test_note_requires_reference(self):
        """Test that reference is required."""
        note = BibleNote(reference="", text="Test")
        with pytest.raises(ValidationError):
            note.validate()
    
    def test_note_requires_text(self):
        """Test that text is required."""
        note = BibleNote(reference="John 3:16", text="")
        with pytest.raises(ValidationError):
            note.validate()
    
    def test_note_to_dict(self):
        """Test converting note to dictionary."""
        note = BibleNote(reference="John 3:16", text="Test")
        data = note.to_dict()
        assert data["reference"] == "John 3:16"
        assert data["text"] == "Test"
        assert "created" in data
    
    def test_note_from_dict(self):
        """Test creating note from dictionary."""
        data = {
            "reference": "John 3:16",
            "text": "Test note",
            "created": "2024-01-01T12:00:00"
        }
        note = BibleNote.from_dict(data)
        assert note.reference == "John 3:16"
        assert note.text == "Test note"
```

---

## 7. MAIN APPLICATION ENTRY POINT

### main.py
```python
"""Main application entry point."""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from utils.logger import LoggerSetup
from ui.main_window import BibleReferenceApp

logger = LoggerSetup.get_logger(__name__)

def main():
    """Run the application."""
    logger.info("Starting Bible Reference Application")
    logger.info(f"Data directory: {settings.user_data_dir}")
    
    try:
        app = BibleReferenceApp()
        app.mainloop()
    except Exception as e:
        logger.exception("Application crashed")
        print(f"Error: {e}")
        raise
    finally:
        logger.info("Application closed")

if __name__ == "__main__":
    main()
```

---

## 8. REQUIREMENTS FILES

### requirements.txt
```
# Core dependencies
Pillow>=9.0.0
requests>=2.28.0

# Optional: for database (future)
# sqlalchemy>=2.0.0
# alembic>=1.10.0
```

### requirements-dev.txt
```
-r requirements.txt

# Testing
pytest>=7.0.0
pytest-cov>=3.0.0

# Code quality
black>=22.0.0
flake8>=4.0.0
isort>=5.10.0
mypy>=0.950

# Building
pyinstaller>=5.0.0
wheel>=0.37.0
twine>=3.8.0
```

---

## 9. GITHUB ACTIONS CI/CD

### .github/workflows/tests.yml
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Format check with black
      run: black --check .
    
    - name: Test with pytest
      run: pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Next Steps

1. **Start with config extraction** - Move BOOK_CHAPTERS and constants to `config/constants.py`
2. **Add logging** - Implement `utils/logger.py` and start using it
3. **Create data models** - Move validation logic into `storage/models.py`
4. **Add DataManager** - Replace direct JSON reads with `DataManager` class
5. **Write tests** - Create basic test suite for validators and models
6. **Refactor UI** - Split `main_window.py` into smaller widget modules

This structured approach will make the codebase much easier to maintain, test, and extend.
