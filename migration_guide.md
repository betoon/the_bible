# Migration Guide: From Monolithic to Modular

A step-by-step guide to safely refactor your 3000+ line file into a professional modular structure.

---

## Phase 1: Preparation (Days 1-2)

### Step 1: Create Project Structure
```bash
# Create new directory structure
mkdir -p bible_app/{config,core,storage,ui,utils,tests}
mkdir -p bible_app/ui/widgets
mkdir -p .github/workflows

# Create __init__.py files
touch bible_app/__init__.py
touch bible_app/{config,core,storage,ui,utils,tests}/__init__.py
touch bible_app/ui/widgets/__init__.py
```

### Step 2: Setup Version Control
```bash
# If not already done
git init
git add .
git commit -m "Initial commit before refactoring"

# Create feature branch
git checkout -b refactor/modularize
```

### Step 3: Copy Original File for Reference
```bash
cp bible_app.py _original_bible_app.py  # Keep as backup
```

---

## Phase 2: Extract Configuration (Days 3-5)

### Step 1: Extract Constants

**File: `config/constants.py`**

1. Copy all BOOK_* constants from lines 65-161
2. Copy BIBLE_API_URL, JPS_BASE_URL from lines 51-52
3. Copy STRONGS_PATTERN from line 62
4. Copy all the sample BIBLE data (lines 82-146)

```python
# Add to top of config/constants.py
from typing import Dict, List
import re

# Paste all the constants here
BOOK_CHAPTERS = { ... }
BOOK_ORDER = list(BOOK_CHAPTERS.keys())
# ... etc
```

**Update original file:**
```python
# In bible_app.py, replace all those constants with:
from config.constants import BOOK_CHAPTERS, BOOK_ORDER, BIBLE_API_URL, etc.
```

### Step 2: Extract Settings

**File: `config/settings.py`**

Copy the `default_user_data_dir()` function and all the path definitions (lines 24-50):

```python
from pathlib import Path
import os
import sys

def default_user_data_dir():
    # ... existing code

USER_DATA_DIR = default_user_data_dir()
# ... all other path definitions
```

Then refactor into the Settings class (see refactoring_code_examples.md).

**Update original file:**
```python
from config.settings import settings
# Replace all uses of USER_DATA_DIR, DATA_DIR, etc. with settings.user_data_dir, etc.
```

### Step 3: Colors to Constants

**Update `config/constants.py`:**

```python
# UI Colors
UI_COLORS = {
    "bg_main": "#F3F3F3",
    "bg_panel": "#FFFFFF",
}

# Or in code:
APP_BG = "#F3F3F3"  # Keep existing var names for backward compatibility
APP_PANEL = "#FFFFFF"
```

**In original file, replace:**
```python
# Before
APP_BG = "#F3F3F3"
APP_PANEL = "#FFFFFF"

# After
from config.constants import APP_BG, APP_PANEL
```

---

## Phase 3: Extract Data Models (Days 6-8)

### Step 1: Create Models File

**File: `storage/models.py`**

From the original file, identify all classes that represent data:
- Look for `__init__` methods that store user data
- Examples: note data, bookmarks, journal entries, highlights

Create dataclasses for each (see refactoring_code_examples.md for complete examples).

### Step 2: Find Validation Logic

Search the original file for:
- Input validation in dialogs
- JSON loading/saving with error checking
- Data constraint checks

Extract into model `validate()` methods.

### Step 3: Test Models

Create `tests/test_models.py` with basic tests:
```bash
pytest tests/test_models.py -v
```

---

## Phase 4: Extract Data Persistence (Days 9-11)

### Step 1: Find All JSON Operations

In the original file, search for:
```python
json.load()
json.loads()
json.dump()
json.dumps()
```

Each one is a persistence operation that should move to DataManager.

### Step 2: Create DataManager

**File: `storage/data_manager.py`**

For each type of data (notes, bookmarks, journal, highlights):

1. Create `load_[type]()` method
2. Create `save_[type]()` method
3. Add error handling with logging

Example structure:
```python
def load_notes(self):
    """Load notes from disk."""
    if not self.notes_file.exists():
        return []
    try:
        data = json.loads(self.notes_file.read_text())
        return [BibleNote.from_dict(n) for n in data]
    except json.JSONDecodeError as e:
        logger.error(f"Failed to load notes: {e}")
        raise DataLoadError(f"Corrupted notes file: {e}")
```

### Step 3: Replace Direct File Access

In the original file, replace:
```python
# Before
notes_json = json.loads(NOTES_PATH.read_text())
# do something with notes_json
NOTES_PATH.write_text(json.dumps(notes_json))

# After
notes = data_manager.load_notes()
# do something with notes
data_manager.save_notes(notes)
```

---

## Phase 5: Extract Utilities (Days 12-13)

### Step 1: Logging

**File: `utils/logger.py`**

Copy and refactor the logging setup (if any exists) or create new.

### Step 2: Validators

**File: `utils/validators.py`**

Search original file for:
- Bible reference parsing/validation
- Any input validation functions

Create validators.py with:
```python
class BibleReferenceValidator:
    @staticmethod
    def validate(reference: str) -> bool:
        # validation logic
    
    @staticmethod
    def parse(reference: str) -> tuple:
        # parsing logic
```

### Step 3: Add Helper Functions

**File: `utils/helpers.py`**

Move any utility functions:
- String formatting
- File operations
- Common calculations

---

## Phase 6: Refactor Main Logic (Days 14-18)

### Step 1: Extract Core Bible Logic

**File: `core/bible_data.py`**

Move all methods related to:
- Fetching Bible verses
- Caching verses
- Translation management

Example:
```python
class BibleDataManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
    
    def fetch_verse(self, reference: str, translation: str):
        """Fetch verse from API or cache."""
        # existing logic from original file
    
    def cache_verse(self, reference: str, translation: str, text: str):
        # existing caching logic
```

### Step 2: Extract Study Tools

**File: `core/study_tools.py`**

Move theme, people, and maps related code.

### Step 3: Replace in Main File

In the original app class:
```python
# Before
def fetch_verse(self, reference, translation):
    # 30 lines of logic

# After
def fetch_verse(self, reference, translation):
    return self.bible_data.fetch_verse(reference, translation)
```

---

## Phase 7: Refactor UI (Days 19-23)

### Step 1: Identify UI Components

Break down the main window into components:
- BibleViewer - displays verses
- NotesPanel - manages notes
- StudyToolsPanel - themes, people, etc.
- JournalWindow - separate window
- SettingsWindow - separate window

### Step 2: Create Widget Files

**File: `ui/widgets/bible_viewer.py`**

```python
import tkinter as tk
from tkinter import ttk

class BibleViewer(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()
    
    def build_ui(self):
        """Build the UI."""
        # Extract the relevant UI building code from main file
    
    def display_verse(self, reference, text):
        """Display a verse."""
        # Update UI with verse
```

Repeat for:
- `ui/widgets/notes_panel.py`
- `ui/widgets/journal_window.py`
- etc.

### Step 3: Refactor Main Window

**File: `ui/main_window.py`**

```python
import tkinter as tk
from tkinter import ttk

from ui.widgets.bible_viewer import BibleViewer
from ui.widgets.notes_panel import NotesPanel
from storage.data_manager import DataManager
from core.bible_data import BibleDataManager

class BibleReferenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager(settings.user_data_dir)
        self.bible_data = BibleDataManager(settings.cache_dir)
        self.build_ui()
    
    def build_ui(self):
        """Build main window."""
        # Create the viewer
        self.viewer = BibleViewer(self, self)
        self.viewer.pack(fill="both", expand=True, side="left")
        
        # Create the notes panel
        self.notes = NotesPanel(self, self)
        self.notes.pack(fill="both", expand=True, side="right")
```

---

## Phase 8: Create Tests (Days 24-25)

### Step 1: Unit Tests

**File: `tests/test_validators.py`**

Test validators with pytest (see refactoring_code_examples.md).

**File: `tests/test_models.py`**

Test data models.

**File: `tests/test_data_manager.py`**

```python
import pytest
from pathlib import Path
from storage.data_manager import DataManager
from storage.models import BibleNote

def test_save_and_load_notes(tmp_path):
    """Test saving and loading notes."""
    dm = DataManager(tmp_path)
    
    notes = [
        BibleNote(reference="John 3:16", text="Test 1"),
        BibleNote(reference="Psalm 23", text="Test 2"),
    ]
    
    dm.save_notes(notes)
    loaded = dm.load_notes()
    
    assert len(loaded) == 2
    assert loaded[0].reference == "John 3:16"
```

### Step 2: Integration Tests

Test the whole flow:
```python
def test_user_adds_note_and_saves(app, tmp_path):
    """Test user workflow of adding and saving a note."""
    # Simulate user adding a note
    # Verify it's saved to disk
    # Verify it loads correctly
```

---

## Phase 9: Migration Execution

### Step 1: Create a New Main Entry Point

**File: `main.py`**

```python
#!/usr/bin/env python3
"""Main application entry point."""

import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from utils.logger import LoggerSetup
from ui.main_window import BibleReferenceApp

logger = LoggerSetup.get_logger(__name__)

def main():
    logger.info("Starting Bible Reference Application")
    app = BibleReferenceApp()
    app.mainloop()

if __name__ == "__main__":
    main()
```

### Step 2: Run Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html
```

### Step 3: Verify All Features Work

Create a checklist:
- [ ] Can load and display Bible verses
- [ ] Can add and save notes
- [ ] Can save bookmarks
- [ ] Can create journal entries
- [ ] Settings persist
- [ ] Offline mode works
- [ ] All study tools function

### Step 4: Merge to Main

```bash
git add .
git commit -m "feat: modularize application into separate modules"
git checkout main
git merge refactor/modularize
```

---

## Troubleshooting Guide

### Problem: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'config'`

**Solution:**
```python
# In main.py or __init__.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Problem: Circular Imports

**Symptom:** `ImportError: cannot import name 'X' from partially initialized module 'Y'`

**Solution:**
```python
# Move imports into functions if needed
def load_data():
    from storage.data_manager import DataManager  # Import here
    return DataManager()

# Or restructure to avoid circular dependencies
# - core imports utils but not ui
# - ui imports core but not core
```

### Problem: Settings Not Available

**Symptom:** `NameError: name 'settings' is not defined`

**Solution:**
```python
# Make sure to import settings at the top
from config.settings import settings

# Use throughout
data_dir = settings.user_data_dir
```

### Problem: Data Loss During Migration

**Prevent it:**
```bash
# Before any changes, backup user data
cp -r ~/.local/share/BibleReferenceApp ~/.local/share/BibleReferenceApp.backup

# Run with old version to verify data loads
python _original_bible_app.py
```

---

## Commit Strategy

Make commits for each logical step:

```bash
git commit -m "refactor: extract constants to config/constants.py"
git commit -m "refactor: extract settings to config/settings.py"
git commit -m "feat: create data models in storage/models.py"
git commit -m "refactor: create DataManager for persistence"
git commit -m "refactor: extract validators to utils/"
git commit -m "refactor: create BibleDataManager in core/"
git commit -m "refactor: split UI into separate widget modules"
git commit -m "test: add unit tests for validators and models"
git commit -m "test: add integration tests"
git commit -m "chore: add logging and error handling"
```

This makes it easier to review, revert if needed, and understand what changed.

---

## Estimated Timeline

- **Phase 1**: 2 days (setup)
- **Phase 2**: 3 days (config)
- **Phase 3**: 3 days (models)
- **Phase 4**: 3 days (persistence)
- **Phase 5**: 2 days (utilities)
- **Phase 6**: 5 days (core logic)
- **Phase 7**: 5 days (UI refactoring)
- **Phase 8**: 2 days (testing)
- **Phase 9**: 2 days (integration & merge)

**Total: ~27 days (or 4-5 weeks part-time)**

If you work ~2 hours per day, this is very achievable.

---

## Success Criteria

When you're done, you should have:

✅ Code organized into logical modules
✅ No circular imports
✅ All tests passing
✅ All features working as before
✅ Error handling throughout
✅ Logging configured
✅ Can run with: `python main.py`
✅ Can run tests with: `pytest tests/ -v`
✅ Can build executable with: `pyinstaller main.py`
✅ User data persists correctly
✅ Easy to add new features

---

## After Refactoring: Next Steps

Once modularized, you can easily:

1. **Add new features** - Create new modules without touching existing code
2. **Write tests** - Each module can be tested independently
3. **Optimize performance** - Profile and improve specific modules
4. **Improve UI** - Swap Tkinter for PyQt6 without touching business logic
5. **Add database** - Replace JSON with database in DataManager only
6. **Deploy to cloud** - Extract UI into web frontend while reusing core logic
7. **Create CLI** - Reuse core logic for command-line version
8. **Publish as package** - Core logic becomes reusable library

The modular structure enables all of these without major rewrites.
