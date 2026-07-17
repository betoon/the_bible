"""Search across Bible text and personal study resources."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from bible_app.core.hymns import read_hymnal_index_cache
from bible_app.ui.window_config import configure_window_size


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


class SearchEverythingWindow(tk.Toplevel):
    def __init__(self, app, people=None, maps=None, map_viewer_class=None, document_viewer_class=None):
        super().__init__(app)
        self.app = app
        self.people = people or {}
        self.maps = maps or []
        self.map_viewer_class = map_viewer_class
        self.document_viewer_class = document_viewer_class
        self.targets = []
        self.title("Search Everything")
        configure_window_size(self, "search_everything", "820x640", (680, 500))

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

        self.search_bible_text(query)
        self.search_personal_study(query)
        self.search_library(query)
        self.search_hymns(query)

        if not self.targets:
            self.add_result("No matches found.")

    def search_bible_text(self, query):
        for ref, text in self.app.all_references():
            if query in text.lower() or query in ref.lower():
                self.add_result(f"Bible: {ref} - {text[:90]}", ("ref", ref))
                if len(self.targets) >= 80:
                    break

    def search_personal_study(self, query):
        for ref, note in self.app.notes.items():
            if query in note.lower() or query in ref.lower():
                self.add_result(f"Note: {ref} - {note[:90]}", ("ref", ref))

        for entry in self.app.journal_entries:
            haystack = " ".join(str(entry.get(key, "")) for key in ("reference", "reflection", "prayer")).lower()
            if query in haystack:
                self.add_result(f"Journal: {entry.get('reference', '')} - {entry.get('reflection', '')[:90]}", ("ref", entry.get("reference", "")))

        for name, person in self.people.items():
            if query in name.lower() or query in person.get("summary", "").lower():
                self.add_result(f"Person: {name} - {person.get('summary', '')[:90]}", ("person", name))

        for item in self.maps:
            if query in searchable_map_text(item):
                self.add_result(f"Map: {item.get('title', '')}", ("map", item))

    def search_library(self, query):
        for doc in self.app.library_documents:
            if query in doc.get("title", "").lower() or query in doc.get("text", "").lower():
                self.add_result(f"Document: {doc.get('title', '')}", ("document", doc))

    def search_hymns(self, query):
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
        elif kind == "map" and self.map_viewer_class:
            self.map_viewer_class(self.app, value)
        elif kind == "document" and self.document_viewer_class:
            self.document_viewer_class(self.app, value)
