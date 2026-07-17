"""People reference and profile windows."""

import tkinter as tk
from tkinter import ttk

from bible_app.ui.window_config import configure_window_size


class PeopleReferenceWindow(tk.Toplevel):
    def __init__(self, app, people=None, people_reference=None, person_window_class=None):
        super().__init__(app)
        self.app = app
        self.people = people or {}
        self.people_reference = people_reference or {}
        self.person_window_class = person_window_class or PersonWindow
        self.title("People Reference")
        configure_window_size(self, "people_explorer", "860x680", (720, 540))
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
        self.build_group_tab(family_tab, self.people_reference.get("family_trees", []), "people")
        self.build_group_tab(kings_tab, self.people_reference.get("kings_timeline", []), "name")
        self.build_group_tab(prophets_tab, self.people_reference.get("prophets_timeline", []), "name")
        self.build_group_tab(apostles_tab, self.people_reference.get("apostles", []), "name")

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
        for name in sorted(self.people):
            entry = self.people[name]
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
        person = self.people.get(name, {})
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
            self.person_window_class(self.app, self.visible_people[index], self.people)

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
            if refs.curselection():
                self.app.open_reference(refs.get(refs.curselection()[0]))

        left.bind("<<ListboxSelect>>", show_item)
        refs.bind("<<ListboxSelect>>", open_ref)
        if entries:
            left.selection_set(0)
            show_item()


class PersonWindow(tk.Toplevel):
    def __init__(self, app, name, people=None, maps_for_person_func=None, map_viewer_class=None):
        super().__init__(app)
        self.app = app
        self.name = name
        self.people = people or {}
        self.maps_for_person = maps_for_person_func or (lambda _name: [])
        self.map_viewer_class = map_viewer_class
        self.person = self.people[name]
        self.title(f"Person - {name}")
        configure_window_size(self, "person_profile", "760x820", (620, 580))
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
        self.person_maps = self.maps_for_person(self.name)
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
            marker = "" if related in self.people else " (not added yet)"
            self.related_list.insert("end", f"{related}{marker}")
        self.related_list.bind("<<ListboxSelect>>", self.on_related_selected)

    def on_reference_selected(self, _event=None):
        if self.reference_list.curselection():
            index = self.reference_list.curselection()[0]
            if index < len(self.references):
                self.app.open_reference(self.references[index])

    def on_mention_selected(self, _event=None):
        if self.mention_list.curselection():
            index = self.mention_list.curselection()[0]
            if index < len(self.mention_refs):
                self.app.open_reference(self.mention_refs[index])

    def on_map_selected(self, _event=None):
        if not self.person_map_list.curselection() or not self.person_maps or not self.map_viewer_class:
            return
        index = self.person_map_list.curselection()[0]
        if index < len(self.person_maps):
            self.map_viewer_class(self.app, self.person_maps[index])

    def on_related_selected(self, _event=None):
        if not self.related_list.curselection():
            return
        index = self.related_list.curselection()[0]
        if index < len(self.related_people) and self.related_people[index] in self.people:
            PersonWindow(self.app, self.related_people[index], self.people, self.maps_for_person, self.map_viewer_class)
