"""Small in-memory caches for hot Bible lookup data."""

from collections import OrderedDict


class LruMemoryCache:
    """Tiny least-recently-used cache for hot in-session values."""

    def __init__(self, max_size=512):
        """Create a cache that keeps at most ``max_size`` entries."""
        self.max_size = max(1, int(max_size))
        self._items = OrderedDict()

    def get(self, key, default=None):
        """Return a value and mark it recently used, or ``default``."""
        if key not in self._items:
            return default
        value = self._items.pop(key)
        self._items[key] = value
        return value

    def set(self, key, value):
        """Store a value, evicting the oldest entry when full."""
        if key in self._items:
            self._items.pop(key)
        self._items[key] = value
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)
        return value

    def clear(self):
        """Remove every cached item."""
        self._items.clear()

    def __len__(self):
        return len(self._items)


class BibleLookupCache:
    """Cache repeated Bible passage text and reference-list lookups."""

    def __init__(self, max_passages=1024):
        """Create passage and reference caches for the current app session."""
        self.passages = LruMemoryCache(max_passages)
        self.references = {}

    def get_passage(self, translation, ref):
        """Return cached passage text for a translation/reference pair."""
        return self.passages.get((translation, ref))

    def set_passage(self, translation, ref, text):
        """Cache passage text for a translation/reference pair."""
        return self.passages.set((translation, ref), text)

    def get_references(self, translation):
        """Return cached ``(reference, text)`` tuples for a translation."""
        return self.references.get(translation)

    def set_references(self, translation, references):
        """Cache all searchable references for a translation."""
        self.references[translation] = references
        return references

    def clear(self, translation=None):
        """Clear all caches, or only entries for one translation."""
        if translation is None:
            self.passages.clear()
            self.references.clear()
            return
        for key in list(self.passages._items):
            if key[0] == translation:
                self.passages._items.pop(key, None)
        self.references.pop(translation, None)
