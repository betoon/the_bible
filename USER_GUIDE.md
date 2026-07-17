# Bible Reference Study Tool - User Guide

## Starting The App

Open the project folder and run:

```text
Launch_Bible_Reference.bat
```

You can also run the Python app directly:

```text
python bible_reference_app.py
```

The app stores your notes, journal entries, study sessions, document library, hymnal index cache, and backups in your local Bible Reference Study Tool data folder.

## Main Screen

The main screen has three study areas:

- Left panel: translation, books, chapters, search, themes, people, bookmarks, and library tools.
- Center reader: the current chapter or passage.
- Right panel: cross references, maps, people, hymns, commentary, and personal notes.

The top toolbar is grouped into menus:

- Study: dashboard, worksheet, binder, sessions, and reading plans.
- Search: search everything, word study, translation comparison, and statistics.
- Explore: timeline, cross-reference graph, and presentation mode.
- Manage: tags, exports, and settings.
- Help: quick help, the reference guide, and the developer guide.

The bottom status bar shows feedback such as loaded library status, downloads, imports, bookmarks, and saved notes.

Use F1 or Help > Open Help to open the in-app help window.

## Opening A Passage

Type a reference into the passage box and choose Open Passage.

Examples:

```text
John 3:16
Psalm 23
Romans 8:1-4
Jn 1:1
1Corinthians 13
```

Back and Forward move through passages you have opened during the session.

## Translations And Offline Reading

Use the translation selector in the left panel to change translations.

KJV and JPS 1917 can fetch missing chapters online and cache them locally. The Library Manager can download larger sections for offline use, including:

- Current book
- New Testament
- Hebrew Bible / Old Testament
- Torah
- Prophets
- Writings

NIV, ESV, and other copyrighted translations require a compatible local JSON file that you are allowed to use.

## Searching

Use the left-panel search for Bible text searches within the selected range.

Use Search > Search Everything to search across more of your study material, including Bible text, notes, journal entries, people, maps, documents, and hymns.

Use Search > Word Study to find word occurrences and related usage.

Use Search > Compare Translations to view the selected verse or passage across installed translations.

## Notes And Journal

Personal notes are tied to the selected verse or passage. Notes auto-save after you pause typing.

The notes editor supports:

- Save Note
- Clear
- Undo
- Redo
- Ctrl+Z
- Ctrl+Y

Use Journal This to create a private journal entry connected to the current passage. Journal entries can include reflection, prayer, and image links.

## Study Worksheets

Use Study > Passage Worksheet to open a structured worksheet for the current passage.

Worksheet fields include:

- Observation
- Interpretation
- Application
- Questions
- Prayer
- Related Hymn
- Tags

This is useful for sermon prep, classes, personal study, or keeping a repeated study method.

## Study Sessions And Binder

Use Study > Study Sessions to collect passages and notes into a named study session.

Use Study > Study Binder for a broader study workspace that can gather:

- Passages
- Notes
- People
- Maps
- Hymns
- Imported documents
- Exported study packets

## Themes And Concepts

The Theme and Concept tools help trace ideas across Scripture.

When you open a passage, the app can show related themes and smart suggestions based on the passage text and existing concept library. You can add passages to concepts and export concept notes.

## Cross References

The right panel shows cross references for the selected passage. You can also open:

- Cross-reference explorer
- Cross-reference graph
- User-created links

These are helpful for tracing related verses, themes, people, places, and repeated ideas.

## People, Maps, And Timeline

The People tools show people connected to the current passage and provide a larger people reference window.

The Maps section can show map notes and open local map images when available.

Use Explore > Timeline to view biblical people, events, books, and historical periods in sequence.

## Hymnal Reader

Place PDF hymnals in:

```text
data\hymnals
```

Open the hymnal reader from the right panel. The first time a hymnal is opened, the app scans the PDF and builds an index. Later openings use the saved index unless the PDF changes.

The hymnal reader can:

- Browse hymns from a left menu
- Search hymn titles and sections
- View sheet music
- View extracted text
- Favorite hymns
- Show recent hymns
- Link a hymn to the current passage
- Add a hymn to the current study session
- Open the original PDF externally

## Document Library

Use Library Manager > Convert Document to add supported local documents to the searchable library.

Supported document types:

- PDF
- DOCX
- TXT
- Markdown
- HTML

Converted documents can be searched and opened from the Library Manager and Search Everything.

## Exports

The app can export notes, journal entries, study packets, sessions, and concept notes to Markdown.

Exports are saved in the app's exports folder under your local Bible Reference Study Tool data folder.

## Backups And Data Safety

The app creates backups before important data writes and can create startup backups of the user data folder.

Backups are stored in:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool\backups
```

If a JSON file is damaged, the app quarantines a copy and falls back to safe defaults so the app can keep opening without silently destroying the damaged file.

## Settings

Use Manage > Settings to adjust:

- Reader background color
- Reader text color
- Highlight color
- Font
- Font size
- Light or dark reader mode

Configuration defaults live in:

```text
bible_app\config\settings.ini
```

## Troubleshooting

If a chapter does not open, check that the selected translation contains that book and chapter. For KJV or JPS 1917, the app may be able to fetch and cache the chapter online.

If a hymnal has no sheet music view, make sure the PDF is readable and that PDF rendering support is installed.

If a converted document has little text, the source may be scanned images rather than selectable text.

If the app reports offline mode, local cached chapters and imported translations still work.

If something unexpected happens, check the logs folder:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool\logs
```
