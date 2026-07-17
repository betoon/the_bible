"""Private journal popup window."""

from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bible_app.storage.user_data import write_journal
from bible_app.ui.window_config import configure_window_size


class JournalWindow(tk.Toplevel):
    def __init__(self, app, reference, verse_text):
        super().__init__(app)
        self.app = app
        self.reference = reference
        self.verse_text = verse_text
        self.image_paths = []
        self.title(f"Private Journal - {reference}")
        configure_window_size(self, "journal", "760x680", (620, 520))
        self.build_ui()
        self.load_existing_entries()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Journal This: {self.reference}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text=self.verse_text, style="Muted.TLabel", wraplength=710).pack(anchor="w", pady=(4, 12))

        ttk.Label(root, text="Reflection / Notes", style="Section.TLabel").pack(anchor="w")
        self.reflection_text = tk.Text(root, height=8, wrap="word")
        self.reflection_text.pack(fill="both", expand=True, pady=(4, 10))

        ttk.Label(root, text="Prayer", style="Section.TLabel").pack(anchor="w")
        self.prayer_text = tk.Text(root, height=6, wrap="word")
        self.prayer_text.pack(fill="both", expand=True, pady=(4, 10))

        image_row = ttk.Frame(root)
        image_row.pack(fill="x", pady=(0, 8))
        ttk.Button(image_row, text="Add Image Link", command=self.add_image).pack(side="left")
        ttk.Button(image_row, text="Save Journal Entry", command=self.save_entry, style="Primary.TButton").pack(side="right")
        self.image_label = ttk.Label(root, text="No images linked yet.", style="Muted.TLabel", wraplength=710)
        self.image_label.pack(anchor="w", pady=(0, 10))

        ttk.Label(root, text="Previous Journal Entries For This Passage", style="Section.TLabel").pack(anchor="w")
        self.entries_list = tk.Listbox(root, height=7, exportselection=False)
        self.entries_list.pack(fill="x", pady=(4, 0))

    def add_image(self):
        path = filedialog.askopenfilename(
            title="Link Image To Journal Entry",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.webp;*.tif;*.tiff"), ("All files", "*.*")],
        )
        if not path:
            return
        self.image_paths.append(path)
        self.image_label.configure(text="\n".join(self.image_paths))

    def load_existing_entries(self):
        self.entries_list.delete(0, "end")
        matches = [entry for entry in self.app.journal_entries if entry.get("reference") == self.reference]
        if not matches:
            self.entries_list.insert("end", "No journal entries for this passage yet.")
            return
        for entry in matches[-20:]:
            created = entry.get("created", "")
            summary = (entry.get("reflection", "") or entry.get("prayer", "")).replace("\n", " ")[:70]
            self.entries_list.insert("end", f"{created} - {summary}")

    def save_entry(self):
        reflection = self.reflection_text.get("1.0", "end").strip()
        prayer = self.prayer_text.get("1.0", "end").strip()
        if not reflection and not prayer and not self.image_paths:
            messagebox.showinfo("Private Journal", "Add a reflection, prayer, or image before saving.")
            return
        entry = {
            "created": datetime.now().isoformat(timespec="seconds"),
            "reference": self.reference,
            "verse": self.verse_text,
            "reflection": reflection,
            "prayer": prayer,
            "images": list(self.image_paths),
        }
        self.app.journal_entries.append(entry)
        write_journal(self.app.journal_entries)
        self.reflection_text.delete("1.0", "end")
        self.prayer_text.delete("1.0", "end")
        self.image_paths = []
        self.image_label.configure(text="No images linked yet.")
        self.load_existing_entries()
        messagebox.showinfo("Private Journal", "Journal entry saved.")
