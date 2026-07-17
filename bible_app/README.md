# bible_app Package

This package is the modular home for the Bible Reference Study Tool.

The refactor is intentionally phased:

1. Pure helpers move first: paths, storage, references, search, hymn indexing/rendering.
2. Data services move next: study data, documents, maps, translations, and Bible caching.
3. UI windows move one at a time.
4. `BibleReferenceApp` moves last, once the supporting code is smaller and tested.

For now, `bible_reference_app.py` remains the main working application file and imports selected helpers from this package.

