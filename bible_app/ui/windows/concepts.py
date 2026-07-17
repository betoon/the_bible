"""Concept study library window."""

from datetime import datetime
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from bible_app.config.paths import EXPORT_DIR
from bible_app.core.references import normalized_reference
from bible_app.storage.user_data import write_concepts
from bible_app.ui.window_config import configure_window_size
from bible_app.utils.helpers import markdown_line


class ConceptLibraryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = None
        self.title("Concept Study Library")
        configure_window_size(self, "concept_library", "960x680", (760, 540))
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Concept Study Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Study ideas, doctrines, historical topics, Apocrypha-related readings, and personal research trails.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(4, 10))

        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=3)

        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Button(search_row, text="New", command=self.new_concept).pack(side="left", padx=(6, 0))

        self.concept_list = tk.Listbox(left, exportselection=False)
        self.concept_list.pack(fill="both", expand=True)
        self.concept_list.bind("<<ListboxSelect>>", self.on_concept_selected)

        ttk.Label(right, text="Name", style="Section.TLabel").pack(anchor="w")
        self.name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.name_var).pack(fill="x", pady=(4, 8))
        ttk.Label(right, text="Category", style="Section.TLabel").pack(anchor="w")
        self.category_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.category_var).pack(fill="x", pady=(4, 8))
        ttk.Label(right, text="Summary", style="Section.TLabel").pack(anchor="w")
        self.summary_text = tk.Text(right, height=5, wrap="word")
        self.summary_text.pack(fill="x", pady=(4, 8))

        lower = ttk.Frame(right)
        lower.pack(fill="both", expand=True)
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(1, weight=1)
        ttk.Label(lower, text="Bible References", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(lower, text="Related Readings / Sources", style="Section.TLabel").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.references_list = tk.Listbox(lower, height=8, exportselection=False)
        self.references_list.grid(row=1, column=0, sticky="nsew", pady=(4, 8))
        self.references_list.bind("<Double-Button-1>", self.open_selected_reference)
        self.readings_text = tk.Text(lower, height=8, wrap="word")
        self.readings_text.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(4, 8))

        ref_buttons = ttk.Frame(lower)
        ref_buttons.grid(row=2, column=0, sticky="ew")
        ttk.Button(ref_buttons, text="Add Current Passage", command=self.add_current_reference).pack(side="left", fill="x", expand=True)
        ttk.Button(ref_buttons, text="Add Typed Reference", command=self.add_typed_reference).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(ref_buttons, text="Remove Reference", command=self.remove_reference).pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(right, text="My Notes", style="Section.TLabel").pack(anchor="w", pady=(8, 0))
        self.notes_text = tk.Text(right, height=5, wrap="word")
        self.notes_text.pack(fill="x", pady=(4, 8))
        buttons = ttk.Frame(right)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Save Concept", command=self.save_concept, style="Primary.TButton").pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Delete", command=self.delete_concept).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(buttons, text="Export Concept Notes", command=self.export_current_concept).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        self.visible_indices = []
        self.concept_list.delete(0, "end")
        for index, concept in enumerate(self.app.concepts):
            haystack = " ".join([
                concept.get("name", ""),
                concept.get("category", ""),
                concept.get("summary", ""),
                " ".join(concept.get("related_readings", [])),
                " ".join(concept.get("sources", [])),
            ]).lower()
            if query and query not in haystack:
                continue
            self.visible_indices.append(index)
            self.concept_list.insert("end", f"{concept.get('name', '')} - {concept.get('category', '')}")
        if self.current_index in self.visible_indices:
            self.concept_list.selection_set(self.visible_indices.index(self.current_index))

    def on_concept_selected(self, _event=None):
        if not self.concept_list.curselection():
            return
        visible_index = self.concept_list.curselection()[0]
        if visible_index < len(self.visible_indices):
            self.current_index = self.visible_indices[visible_index]
            self.load_concept(self.current_index)

    def load_concept(self, index):
        concept = self.app.concepts[index]
        self.name_var.set(concept.get("name", ""))
        self.category_var.set(concept.get("category", ""))
        self.set_edit_text(self.summary_text, concept.get("summary", ""))
        self.references_list.delete(0, "end")
        for ref in concept.get("references", []):
            preview = self.app.verse_text(ref)
            self.references_list.insert("end", f"{ref} - {preview[:70]}" if preview else ref)
        readings = list(concept.get("related_readings", []))
        sources = list(concept.get("sources", []))
        text = ""
        if readings:
            text += "Related readings:\n" + "\n".join(readings)
        if sources:
            text += ("\n\n" if text else "") + "Sources:\n" + "\n".join(sources)
        self.set_edit_text(self.readings_text, text)
        self.set_edit_text(self.notes_text, concept.get("notes", ""))

    def set_edit_text(self, widget, text):
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    def new_concept(self):
        now = datetime.now().isoformat(timespec="seconds")
        self.app.concepts.append({
            "name": "New Concept",
            "category": "Personal Study",
            "summary": "",
            "references": [],
            "related_readings": [],
            "notes": "",
            "sources": [],
            "created": now,
            "updated": now,
        })
        self.current_index = len(self.app.concepts) - 1
        write_concepts(self.app.concepts)
        self.refresh()
        self.load_concept(self.current_index)

    def current_references(self):
        refs = []
        for index in range(self.references_list.size()):
            raw = self.references_list.get(index).split(" - ", 1)[0].strip()
            if raw:
                refs.append(normalized_reference(raw))
        return refs

    def parse_readings_and_sources(self):
        readings = []
        sources = []
        target = readings
        for raw_line in self.readings_text.get("1.0", "end").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lower = line.lower().rstrip(":")
            if lower == "related readings":
                target = readings
                continue
            if lower == "sources":
                target = sources
                continue
            target.append(line.lstrip("- ").strip())
        return readings, sources

    def save_concept(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showinfo("Concept Study Library", "Give this concept a name before saving.")
            return
        if self.current_index is None:
            self.new_concept()
        readings, sources = self.parse_readings_and_sources()
        concept = self.app.concepts[self.current_index]
        concept.update({
            "name": name,
            "category": self.category_var.get().strip(),
            "summary": self.summary_text.get("1.0", "end").strip(),
            "references": self.current_references(),
            "related_readings": readings,
            "notes": self.notes_text.get("1.0", "end").strip(),
            "sources": sources,
            "updated": datetime.now().isoformat(timespec="seconds"),
        })
        write_concepts(self.app.concepts)
        self.refresh()
        self.app.library_status.set(f"Saved concept: {name}")

    def add_current_reference(self):
        if self.current_index is None:
            self.new_concept()
        ref = normalized_reference(self.app.selected_ref)
        if ref not in self.current_references():
            self.references_list.insert("end", ref)
        self.save_concept()

    def add_typed_reference(self):
        ref = simpledialog.askstring("Add Reference", "Enter a Bible reference:", parent=self)
        if not ref:
            return
        normalized = normalized_reference(ref)
        if normalized not in self.current_references():
            self.references_list.insert("end", normalized)
        self.save_concept()

    def remove_reference(self):
        if self.references_list.curselection():
            self.references_list.delete(self.references_list.curselection()[0])
            self.save_concept()

    def open_selected_reference(self, _event=None):
        if not self.references_list.curselection():
            return
        raw = self.references_list.get(self.references_list.curselection()[0]).split(" - ", 1)[0].strip()
        if raw:
            self.app.open_reference(raw)

    def delete_concept(self):
        if self.current_index is None or self.current_index >= len(self.app.concepts):
            return
        if not messagebox.askyesno("Concept Study Library", "Delete this concept?"):
            return
        self.app.concepts.pop(self.current_index)
        write_concepts(self.app.concepts)
        self.current_index = None
        self.name_var.set("")
        self.category_var.set("")
        self.set_edit_text(self.summary_text, "")
        self.set_edit_text(self.readings_text, "")
        self.set_edit_text(self.notes_text, "")
        self.references_list.delete(0, "end")
        self.refresh()

    def export_current_concept(self):
        if self.current_index is None:
            return
        self.save_concept()
        concept = self.app.concepts[self.current_index]
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^A-Za-z0-9_-]+", "-", concept.get("name", "concept")).strip("-") or "concept"
        path = EXPORT_DIR / f"concept-{name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [
            f"# {concept.get('name', '')}",
            "",
            f"Category: {concept.get('category', '')}",
            "",
            "## Summary",
            concept.get("summary", ""),
            "",
            "## References",
        ]
        for ref in concept.get("references", []):
            lines.extend([f"### {ref}", "", markdown_line(self.app.passage_text(ref)), ""])
        lines.extend(["## Related Readings", ""])
        lines.extend(f"- {item}" for item in concept.get("related_readings", []))
        lines.extend(["", "## Sources", ""])
        lines.extend(f"- {item}" for item in concept.get("sources", []))
        lines.extend(["", "## Notes", "", concept.get("notes", "")])
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Concept Study Library", f"Export saved to:\n{path}")
