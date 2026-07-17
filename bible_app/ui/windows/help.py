"""In-app help window for the Bible Reference Study Tool."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from bible_app import __app_name__, __version__
from bible_app.ui.window_config import configure_window_size


class HelpWindow(tk.Toplevel):
    """Show quick help and links to the full user/developer guides."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.project_dir = Path(__file__).resolve().parents[3]
        self.title("Help")
        configure_window_size(self, "help", "820x640", (680, 500))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Bible Reference Study Tool Help", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text=f"{__app_name__} v{__version__}. Quick reminders for the main workflow. Use the buttons below for the complete guides.",
            style="Muted.TLabel",
            wraplength=760,
        ).pack(anchor="w", pady=(4, 10))

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(buttons, text="Open Reference Guide", command=lambda: self.open_doc("REFERENCE_GUIDE.md")).pack(side="left")
        ttk.Button(buttons, text="Open Developer Guide", command=lambda: self.open_doc("DEVELOPERS_GUIDE.md")).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Open User Guide", command=lambda: self.open_doc("USER_GUIDE.md")).pack(side="left", padx=(8, 0))

        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True)
        self.add_tab(tabs, "Getting Started", GETTING_STARTED_HELP)
        self.add_tab(tabs, "Study Tools", STUDY_TOOLS_HELP)
        self.add_tab(tabs, "Data Safety", DATA_SAFETY_HELP)
        self.add_tab(tabs, "Shortcuts", SHORTCUTS_HELP)

    def add_tab(self, tabs, title, content):
        frame = ttk.Frame(tabs, padding=8)
        tabs.add(frame, text=title)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10)
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", content.strip())
        text.configure(state="disabled")
        scrollbar.config(command=text.yview)

    def open_doc(self, filename):
        path = self.project_dir / filename
        if not path.exists():
            messagebox.showinfo("Help", f"Could not find {filename}.")
            return
        try:
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Help", f"Could not open {filename}:\n{exc}")


GETTING_STARTED_HELP = """
1. Choose a translation in the left panel.
2. Choose a book and chapter, or type a passage like John 3:16.
3. Click a verse in the center reader to make it the active passage.
4. Use the right panel for cross references, maps, related hymns, commentary, and personal notes.
5. Watch the bottom status bar for save, download, and import messages.

KJV and JPS 1917 can fetch missing chapters online and save them for later. Imported translations stay local.
"""


STUDY_TOOLS_HELP = """
Study menu:
- Home Dashboard shows a study starting point.
- Passage Worksheet gives Observation, Interpretation, Application, Questions, Prayer, Related Hymn, and Tags.
- Save Web Commentary stores a local Markdown study copy from a commentary page URL.
- Study Binder gathers passages, notes, people, maps, hymns, and documents.
- Study Sessions collect material for a topic, class, sermon, or personal study.
- Reading Plans help track daily reading.
- Chapter A Day 2026 appears in Reading Plans with a SOAP worksheet for each day.

Search menu:
- Search Everything scans Bible text and your saved study material.
- Word Study finds word occurrences.
- Compare Translations shows the selected passage across installed translations.

Explore menu:
- Timeline connects books, people, and events.
- Cross Reference Graph visualizes related passages.
- Presentation Mode gives a cleaner teaching view.
"""


DATA_SAFETY_HELP = """
Your notes, journals, sessions, worksheets, bookmarks, imported documents, and hymn links are saved outside the program files in your local app data folder.

The app creates backups before important writes and quarantines damaged JSON files instead of silently deleting them.

Use Library Manager for Bible chapter downloads and document conversion. Use Manage > Export Study Packet for Markdown exports.
"""


SHORTCUTS_HELP = """
Passage navigation:
- Alt+Left: back
- Alt+Right: forward
- F5: refresh current view

Tools:
- Ctrl+F: search
- Ctrl+B: bookmark current passage
- Ctrl+N: journal current passage
- Ctrl+D: settings
- Ctrl+T: tags
- Ctrl+W: word study

Notes:
- Ctrl+Z: undo note edit
- Ctrl+Y: redo note edit
"""
