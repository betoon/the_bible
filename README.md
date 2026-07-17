# Bible Reference Study Tool

This is a first prototype for a local Bible study reference tool.

## Start

Double-click:

```text
Launch_Bible_Reference.bat
```

This opens the Python desktop app:

```text
bible_reference_app.py
```

The original browser prototype is still available as `bible_reference.html`.

For help and guides, see:

```text
REFERENCE_GUIDE.md
USER_GUIDE.md
DEVELOPERS_GUIDE.md
PACKAGING.md
```

## What It Does Now

- Browse by book and chapter
- Click down to individual verses
- Quick passage lookup, such as `John 1:1` or `Psalm 23`
- Search the included sample text like a simple concordance
- Trace small starter themes
- Show teaching notes, cross references, original language notes, and map notes
- Save personal notes locally in `bible_personal_notes.json` when using the Python app
- Reopen personal notes automatically when you return to the same passage
- Keep separate private journal entries in `bible_private_journal.json`
- Show a red/green web access status
- Download the full KJV into `data\kjv_bible.json` for offline reading
- Open missing KJV chapters online on demand and cache them locally for next time
- Import a compatible local Bible JSON file
- Translation choices are available for KJV, NIV, and ESV; copyrighted translations need a licensed/local import
- JPS 1917 Hebrew Bible / Tanakh is available as an online/cache translation
- Local JSON Bible modules in `data\EN-English` are loaded as bundled translations
- Lookups accept common book-name variations such as `john`, `Jn 1:1`, `psalms 23`, and `1Corinthians 13`
- Back and Forward buttons remember passage jumps
- Personal notes auto-save after you stop typing
- Bookmarks keep a simple favorites list
- Passage ranges such as `John 3:16-18`, `Romans 8:1-4`, and `Psalm 23:1-6` are supported
- Notes, journal entries, and bookmarks can be exported to Markdown
- Library Manager shows cached chapter counts and can download the current book or the New Testament
- Library Manager shows installed translations, source type, chapter coverage, verse counts, and Strong's-tagged editions
- Library Manager can download JPS 1917 Old Testament / Hebrew Bible, Torah, Prophets, or Writings
- Setup lets you change reader background color, text color, highlighter color, font, and font size
- Setup can hide or show Strong's tags in tagged Bible modules
- Notes, journal, bookmarks, and Bible-cache writes create timestamped backups
- People search/profile reference with summaries, roles, references, and related people
- People Reference window includes People, Family Trees, Kings Timeline, Prophets Timeline, and Apostles tabs
- Maps / Places Library reads `study_data\maps.json`, stores local images in `maps`, and keeps source/license/attribution metadata with each map
- The reader can open a related map for the selected passage and compare KJV text with an installed Strong's-tagged module
- The reader can compare the selected verse or range across installed translations
- Starter study notes, themes, people, and people-reference data live in `study_data\study_notes.json`, `study_data\themes.json`, `study_data\people.json`, and `study_data\people_reference.json`

## Saved Data

The Python app saves personal data under your Windows local app data folder:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool
```

That keeps notes, journal entries, downloads, and imports working even when you run the packaged `.exe`.

Exports are saved under:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool\exports
```

Automatic backups are saved under:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool\backups
```

## Prototype Data

The prototype starts with a small public-domain KJV sample. You can use **Download Full KJV** to save the whole KJV for offline study, or simply click a missing KJV chapter marked `online`; the app will fetch that chapter and save it locally. JPS 1917 Hebrew Bible / Tanakh works the same way for Old Testament books. Imported translations still need a compatible local JSON file.

## Hebrew Bible / Tanakh

Select `JPS1917 - JPS 1917 Hebrew Bible / Tanakh` from the Translation list. Missing chapters can be opened on demand and cached, or downloaded in larger sections from Library Manager:

```text
Old Testament / Hebrew Bible
Torah
Prophets
Writings
```

## Bundled English Translations

The app loads compatible unrestricted JSON Bible modules from:

```text
data\EN-English
```

These are included by `Bible_Reference_Study_Tool.spec` when you run `build.bat`, along with `study_data`.

NIV and ESV are not bundled because they are copyrighted translations. The app can display them if you import a compatible JSON file you are allowed to use.

Good next steps:

- Add a richer concordance and Strong's-style original language index
- Add curated public-domain or openly licensed map images with complete attribution
- Add more timelines, people, places, and teaching collections
