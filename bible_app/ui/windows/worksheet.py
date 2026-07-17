"""Passage study worksheet popup window."""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from bible_app.core.references import normalized_reference
from bible_app.storage.user_data import write_worksheets
from bible_app.ui.window_config import configure_window_size


class PassageStudyWorksheetWindow(tk.Toplevel):
    FIELDS = [
        ("observation", "Observation"), ("interpretation", "Interpretation"),
        ("application", "Application"), ("questions", "Questions"),
        ("prayer", "Prayer"), ("related_hymn", "Related Hymn"), ("tags", "Tags"),
    ]

    def __init__(self, app, ref):
        super().__init__(app)
        self.app = app
        self.ref = normalized_reference(ref)
        self.widgets = {}
        self.title(f"Study Worksheet - {self.ref}")
        configure_window_size(self, "passage_worksheet", "780x760", (640, 560))

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Study Worksheet: {self.ref}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=self.app.passage_text(self.ref), style="Muted.TLabel", wraplength=720).pack(anchor="w", pady=(4, 10))

        data = self.app.worksheets.get(self.ref, {})
        for key, label in self.FIELDS:
            ttk.Label(root, text=label, style="Section.TLabel").pack(anchor="w", pady=(8, 0))
            widget = tk.Text(root, height=3 if key in {"related_hymn", "tags"} else 4, wrap="word")
            widget.pack(fill="x", pady=(4, 0))
            widget.insert("1.0", data.get(key, ""))
            self.widgets[key] = widget

        ttk.Button(root, text="Save Worksheet", command=self.save, style="Primary.TButton").pack(fill="x", pady=(12, 0))

    def save(self):
        self.app.worksheets[self.ref] = {key: widget.get("1.0", "end").strip() for key, widget in self.widgets.items()}
        self.app.worksheets[self.ref]["updated"] = datetime.now().isoformat(timespec="seconds")
        write_worksheets(self.app.worksheets)
        self.app.render_chapter()
        messagebox.showinfo("Study Worksheet", "Worksheet saved.")
