"""Biblical timeline popup window."""

import tkinter as tk
from tkinter import ttk

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


def maps_for_person(map_items, name):
    matches = []
    for map_item in map_items:
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

    def __init__(self, app, map_items=None):
        super().__init__(app)
        self.app = app
        self.map_items = map_items or []
        self.title("Biblical Timeline")
        configure_window_size(self, "timeline", "820x620", (680, 500))

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
        maps = sorted({item.get("title", "") for person in people for item in maps_for_person(self.map_items, person)[:2]})
        lines = [
            title,
            "",
            f"Primary texts: {refs}",
            "",
            "People:",
            *[f"- {person}" for person in people],
            "",
            "Related maps:",
            *[f"- {item}" for item in maps if item],
        ]
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")
