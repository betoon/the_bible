# Bible Reference Study Tool - Developer Guide

This guide explains how the code is organized, how the app starts, where data is stored, and where to make common changes.

## 1. Current Architecture

The app is in a phased refactor.

The main working app is still:

```text
bible_reference_app.py
```

The modular package is:

```text
bible_app
```

The strategy is:

1. Move pure helpers first.
2. Move storage and data services next.
3. Move popup windows one at a time.
4. Move the main application class last.

This lets the app keep working while the large original script becomes smaller over time.

## 2. Entry Points

Main desktop app:

```text
python bible_reference_app.py
```

Package entry point:

```text
python -m bible_app.main
```

Windows launcher:

```text
Launch_Bible_Reference.bat
```

Debug helper:

```text
run_app_debug.py
```

## 3. Project Layout

```text
bible_app/
  config/
    constants.py
    paths.py
    settings.py
    settings.ini
  core/
    bible_data.py
    cache.py
    documents.py
    hymns.py
    maps.py
    references.py
    search.py
    study_tools.py
    translations.py
  storage/
    backup.py
    data_manager.py
    models.py
    user_data.py
  ui/
    styles.py
    utils.py
    windows/
    widgets/
  utils/
    background.py
    logger.py
    validators.py
tests/
  test_bible_app_modules.py
  test_bible_reference_app.py
```

## 4. Main Application Class

The main Tk app is:

```text
BibleReferenceApp
```

Location:

```text
bible_reference_app.py
```

Responsibilities:

- Build the main window.
- Hold current app state.
- Coordinate left, center, and right panels.
- Open popup windows.
- Load and save user data.
- Render Bible text.
- Handle navigation and selection.
- Connect UI actions to modular helpers.

Important methods:

- `build_style`: applies shared UI styles.
- `build_ui`: creates the top toolbar, body panes, and status bar.
- `build_left`: creates translation, book/chapter, search, theme, people, bookmark, and library controls.
- `build_center`: creates the Bible reader.
- `build_right`: creates cross reference, map, people, hymn, commentary, and notes panels.
- `open_reference`: parses and opens a verse or range.
- `render_all`: refreshes the main panels.
- `render_chapter`: renders the current chapter.
- `select_verse`: sets the active verse/passage and refreshes related panels.
- `save_note`, `auto_save_note`, `clear_note`: personal note handling.
- `request_chapter_fetch`: starts online chapter fetches.
- `start_chapter_batch_download`: starts library downloads.
- `open_help_window`: opens the Help popup.

## 5. Configuration

Config defaults live in:

```text
bible_app/config/settings.ini
```

Runtime access lives in:

```text
bible_app/config/settings.py
```

Important settings:

- App title and window size.
- API URLs and timeouts.
- Default translation.
- Backup behavior.
- Background worker count.
- Passage cache size.
- UI colors.
- Reader defaults.

Environment override pattern:

```text
BIBLE_APP_<SECTION>_<OPTION>
```

Example:

```text
BIBLE_APP_APP_APP_TITLE=My Bible App
```

## 6. Paths

Path definitions live in:

```text
bible_app/config/paths.py
```

Important concepts:

- `APP_DIR`: project or executable directory.
- `RESOURCE_DIR`: bundled resource root.
- `USER_DATA_DIR`: user data folder.
- `DATA_DIR`: downloaded Bible data.
- `DOCUMENT_LIBRARY_DIR`: converted documents.
- `HYMNALS_DIR`: bundled/local hymnal PDFs.
- `BACKUP_DIR`: user backups.
- `EXPORT_DIR`: Markdown exports.

Path environment overrides:

- `BIBLE_APP_APP_DIR`
- `BIBLE_APP_RESOURCE_DIR`
- `BIBLE_APP_USER_DATA_DIR`
- `BIBLE_APP_DATA_DIR`

## 7. User Data Storage

High-level user-data helpers live in:

```text
bible_app/storage/user_data.py
```

Low-level JSON helpers live in:

```text
bible_app/storage/data_manager.py
```

Data manager behavior:

- Reads JSON safely.
- Accepts optional validators.
- Quarantines damaged JSON.
- Writes through a temporary file.
- Uses `os.replace` for safer writes.
- Creates backups before overwriting existing files.

Common data files:

- `bible_personal_notes.json`
- `bible_private_journal.json`
- `bible_bookmarks.json`
- `bible_highlights.json`
- `bible_concepts.json`
- `bible_study_sessions.json`
- `bible_reading_plans.json`
- `bible_study_worksheets.json`
- `bible_hymn_links.json`
- `bible_hymn_favorites.json`
- `bible_recent_hymns.json`
- `bible_recent_references.json`
- `bible_user_cross_references.json`

## 8. Backups

Backup logic lives in:

```text
bible_app/storage/backup.py
```

Important functions/classes:

- `BackupManager`: full user data snapshots.
- `backup_file`: single-file backup before overwrite.
- `quarantine_file`: copy damaged or invalid files for later review.
- `usable_backup_dir`: finds a writable backup location.

Startup backup behavior is controlled by config:

```ini
[storage]
auto_backup_on_startup = true
max_backups = 10
```

## 9. Logging

Logging lives in:

```text
bible_app/utils/logger.py
```

Behavior:

- Uses rotating log files.
- Logs to file and console.
- Falls back to project logs if the local app-data log cannot be opened.
- Keeps logging under the `bible_app` logger namespace.

Typical usage:

```python
from bible_app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

## 10. Background Work

Background task helper:

```text
bible_app/utils/background.py
```

Class:

```text
BackgroundTaskRunner
```

Purpose:

- Run slow work away from the Tkinter UI thread.
- Call success/error callbacks back on Tk using `after`.
- Keep the interface responsive during downloads, imports, document conversion, and hymnal indexing.

Used by:

- Connection checks.
- Chapter fetch.
- KJV install.
- Batch downloads.
- NIV PDF document import.
- Document conversion.
- Hymnal indexing.

## 11. Bible Fetching

Bible network helpers live in:

```text
bible_app/core/bible_data.py
```

Important functions:

- `fetch_url`: network request with retry/backoff.
- `fetch_kjv_chapter`: fetch one KJV chapter.
- `fetch_jps_chapter`: fetch one JPS 1917 chapter.
- `fetch_translation_chapter`: route supported translations.
- `parse_numbered_chapter_text`: parse JPS numbered text.

Network settings:

```ini
[api]
timeout = 20
retry_attempts = 3
connection_check_timeout = 8
```

## 12. Bible Data Shape

Bible text is stored in memory as nested dictionaries:

```python
BIBLE = {
    "KJV": {
        "John": {
            3: [
                "There was a man of the Pharisees...",
                "...",
            ]
        }
    }
}
```

Verse numbers are one-based in the UI.

Python list indexes are zero-based, so verse 16 is stored at index 15.

## 13. Reference Parsing

Reference helpers live in:

```text
bible_app/core/references.py
```

Important functions:

- `canonical_book_name`
- `reference_parts`
- `reference_range_parts`
- `is_range_reference`
- `normalized_reference`

Supported examples:

```text
John 3:16
Psalm 23
Romans 8:1-4
Jn 1:1
1Corinthians 13
```

Validation helpers live in:

```text
bible_app/utils/validators.py
```

## 14. Search

Bible search helpers live in:

```text
bible_app/core/search.py
```

Search Everything UI lives in:

```text
bible_app/ui/windows/search_everything.py
```

Search operates across app data gathered from the main app:

- Bible text.
- Notes.
- Journal entries.
- People.
- Maps.
- Documents.
- Hymn titles.

## 15. Caching

In-session lookup cache:

```text
bible_app/core/cache.py
```

Classes:

- `LruMemoryCache`
- `BibleLookupCache`

Used for:

- Repeated verse text lookups.
- Repeated passage range lookups.
- Translation reference lists.

Configuration:

```ini
[performance]
passage_cache_size = 1024
```

Hymnal index cache is separate and persistent:

```text
hymnal_index_cache.json
```

## 16. Documents

Document conversion helpers:

```text
bible_app/core/documents.py
```

Document windows:

```text
bible_app/ui/windows/library.py
```

Supported document types:

- PDF
- DOCX
- TXT
- Markdown
- HTML

Important functions:

- `convert_document_to_library_item`
- `extract_pdf_text_and_images`
- `extract_docx_text_and_images`
- `read_document_library`
- `write_document_library`

Converted document metadata is stored in:

```text
documents/library.json
```

Extracted images are stored in:

```text
documents/images
```

## 17. Hymnals

Hymnal core helpers:

```text
bible_app/core/hymns.py
```

Hymnal UI:

```text
bible_app/ui/windows/hymnal_viewer.py
```

Important functions:

- `hymnal_files`
- `build_hymnal_index`
- `load_hymnal_index`
- `parse_hymn_page`
- `render_pdf_page_image`

Flow:

1. User opens Hymnal Reader.
2. App lists PDFs from `data/hymnals`.
3. App checks persistent index cache.
4. If cache is valid, app uses it.
5. If cache is missing/stale, app scans the PDF.
6. Selecting a hymn renders the PDF page as sheet music.

## 18. Study Data

Study helpers:

```text
bible_app/core/study_tools.py
```

Study data files:

```text
study_data/study_notes.json
study_data/themes.json
study_data/people.json
study_data/people_reference.json
study_data/maps.json
```

These provide starter material for:

- Themes.
- People.
- Maps.
- Timeline.
- Passage context.

## 19. UI Styling

Centralized styles:

```text
bible_app/ui/styles.py
```

Main class:

```text
AppTheme
```

Entry function:

```text
configure_app_styles(root)
```

Styles include:

- Main frames.
- Panel frames.
- Toolbar frames.
- Status bar.
- Labels.
- Buttons.
- Primary buttons.
- Menu buttons.
- Comboboxes.

## 20. Main UI Windows

Extracted windows live in:

```text
bible_app/ui/windows
```

Important files:

- `dashboard.py`: study dashboard.
- `worksheet.py`: passage worksheet.
- `cross_reference.py`: explorer and graph.
- `timeline.py`: timeline.
- `search_everything.py`: global search.
- `sessions.py`: sessions, reading plans, binder.
- `presentation.py`: presentation view.
- `map_viewer.py`: map image viewer.
- `settings.py`: reader settings.
- `people.py`: people reference and profile windows.
- `concepts.py`: concept study library.
- `library.py`: Library Manager, document conversion, document viewer.
- `hymnal_viewer.py`: hymnal reader.
- `journal.py`: journal window.
- `help.py`: in-app help window.

## 21. Legacy Inline Windows

Some older window class definitions still exist inside:

```text
bible_reference_app.py
```

At the bottom of the file, many are replaced by imports from `bible_app.ui.windows`.

This is intentional during the phased refactor.

When editing a window, check whether the active version is imported from `bible_app/ui/windows`.

Use:

```text
rg "from bible_app.ui.windows" bible_reference_app.py
```

## 22. Adding A New Popup Window

Recommended steps:

1. Create a file under `bible_app/ui/windows`.
2. Add a `tk.Toplevel` class.
3. Keep the window focused on one job.
4. Import it in `bible_reference_app.py`.
5. Add an `open_*_window` method to `BibleReferenceApp`.
6. Add a menu entry if needed.
7. Add tests for non-UI helper logic.

## 23. Adding A New Data File

Recommended steps:

1. Add the path to `bible_app/config/paths.py`.
2. Add read/write helpers to `bible_app/storage/user_data.py`.
3. Add validation or normalization.
4. Use `read_json` and `write_json`.
5. Back up before overwriting user data.
6. Add tests in `tests/test_bible_app_modules.py`.

## 24. Adding A New Bible Translation

If the translation is bundled/local:

1. Put the source data under `data/EN-English` or import compatible JSON.
2. Normalize it in `core/translations.py`.
3. Make sure it maps to the internal Bible shape.
4. Add a label if needed in `config/settings.py`.
5. Test book/chapter/verse lookup.

If the translation is online:

1. Add configuration for the source URL.
2. Add fetch logic in `core/bible_data.py`.
3. Add retry/logging.
4. Respect licensing.
5. Add tests with mocked network calls.

## 25. Adding A New Study Tool

Recommended pattern:

1. Put pure logic in `bible_app/core`.
2. Put persistence in `bible_app/storage`.
3. Put UI in `bible_app/ui/windows`.
4. Connect from `BibleReferenceApp`.
5. Add a grouped toolbar menu item.
6. Add tests for parsing, normalization, and storage.

## 26. Error Handling Pattern

The app should:

- Log technical details.
- Show friendly messages to the user.
- Avoid silent data loss.
- Use backups for user data.
- Keep the UI responsive.

Example pattern:

```python
try:
    result = do_work()
except Exception as exc:
    logger.exception("Could not do work")
    messagebox.showerror("Friendly Title", f"Could not finish:\n{exc}")
```

## 27. Background Task Pattern

Use `BackgroundTaskRunner` for slow work:

```python
self.background.submit(
    lambda: slow_function(arg),
    on_success=self.finish_work,
    on_error=self.fail_work,
)
```

Do not update Tk widgets directly from worker threads.

Use callbacks scheduled by the background runner.

## 28. Testing

Main test module:

```text
tests/test_bible_app_modules.py
```

Run:

```text
python -m unittest tests.test_bible_app_modules
```

Compile check:

```text
python -m compileall -q bible_app bible_reference_app.py
```

Focused compile check:

```text
python -m py_compile bible_reference_app.py
```

Tests currently cover:

- Config.
- Cache.
- Background tasks.
- Reference parsing.
- Search.
- Hymn parsing.
- Storage.
- Backups.
- Network retry helper.
- Document conversion.
- Maps.
- Translations.
- Study data normalization.
- Validators.
- User data models.

## 29. Packaging

Packaging files:

```text
Bible_Reference_Study_Tool.spec
bible_reference_app.spec
build.bat
build_release.bat
PACKAGING.md
```

Bundled resources may include:

- `data`
- `study_data`
- `maps`
- app code

When adding a required resource folder, make sure the PyInstaller spec includes it.

For the full release checklist, see:

```text
PACKAGING.md
```

## 30. Common Maintenance Tasks

Centralize a style:

- Edit `bible_app/ui/styles.py`.

Add a button/menu item:

- Edit `BibleReferenceApp.build_ui`.
- Prefer grouped menus so the toolbar stays clean.

Add a setting:

- Add default to `settings.ini`.
- Add property to `settings.py`.
- Use the setting in code.

Add persistent user data:

- Add path in `paths.py`.
- Add helpers in `user_data.py`.
- Add validation.
- Add tests.

Add a document type:

- Extend `core/documents.py`.
- Update guide files.
- Add conversion tests.

Add a hymnal feature:

- Put PDF parsing/rendering logic in `core/hymns.py`.
- Put UI behavior in `ui/windows/hymnal_viewer.py`.

## 31. Known Refactor Direction

Good next architecture steps:

1. Continue moving active popup windows out of `bible_reference_app.py`.
2. Move main app data-loading into a service object.
3. Move main reader rendering into a widget class.
4. Move left/right panels into separate widget classes.
5. Add more focused tests around app state changes.
6. Add UI smoke tests if a reliable Tk test harness is introduced.

## 32. Important Rule Of Thumb

When changing the app, ask:

- Is this pure logic? Put it in `core`.
- Is this user data? Put it in `storage`.
- Is this a popup? Put it in `ui/windows`.
- Is this a reusable widget? Put it in `ui/widgets`.
- Is this app-wide style? Put it in `ui/styles.py`.
- Is this configuration? Put it in `config/settings.ini` and `settings.py`.
- Is this a filesystem path? Put it in `config/paths.py`.

That keeps the app from growing back into one giant file.
