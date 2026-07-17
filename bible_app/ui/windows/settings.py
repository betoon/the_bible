"""Reader settings popup window."""

import tkinter as tk
from tkinter import colorchooser, font as tkfont, ttk

from bible_app.ui.window_config import configure_window_size


class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Setup")
        configure_window_size(self, "settings", "520x750", (480, 700))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Reader Setup", style="Title.TLabel").pack(anchor="w", pady=(0, 12))

        ttk.Button(root, text="Change Background Color", command=lambda: self.pick_color("reader_bg")).pack(fill="x", pady=(0, 8))
        ttk.Button(root, text="Change Text Color", command=lambda: self.pick_color("reader_fg")).pack(fill="x", pady=(0, 8))
        ttk.Button(root, text="Pick Highlighter Color", command=lambda: self.pick_color("highlight_bg")).pack(fill="x", pady=(0, 12))

        mode_frame = ttk.Frame(root)
        mode_frame.pack(fill="x", pady=(0, 12))
        ttk.Button(mode_frame, text="Dark Mode", command=self.app.apply_dark_mode).pack(side="left", fill="x", expand=True)
        ttk.Button(mode_frame, text="Light Mode", command=self.app.apply_light_mode).pack(side="left", fill="x", expand=True, padx=(8, 0))

        ttk.Label(root, text="Highlighting Instructions", style="Section.TLabel").pack(anchor="w", pady=(8, 4))
        highlight_text = tk.Text(root, height=4, wrap="word", relief="solid", borderwidth=1)
        highlight_text.pack(fill="x", pady=(0, 12))
        highlight_text.insert("1.0", "1. Select text in the reader\n2. Press Ctrl+H or right-click Highlight\n3. Press Ctrl+U or right-click Remove Highlight\n4. Changes apply immediately")
        highlight_text.configure(state="disabled")

        ttk.Label(root, text="Keyboard Shortcuts", style="Section.TLabel").pack(anchor="w", pady=(8, 4))
        shortcuts_text = tk.Text(root, height=8, wrap="word", relief="solid", borderwidth=1)
        shortcuts_text.pack(fill="x", pady=(0, 12))
        shortcuts = """Ctrl+F - Search    |    Ctrl+B - Bookmark    |    Ctrl+N - Journal
Ctrl+T - Tags      |    Ctrl+W - Word Study  |    Ctrl+D - Settings
Ctrl+H - Highlight |    Ctrl+U - Unhighlight |    Ctrl+, - Dark Mode
Ctrl+. - Light Mode|    Alt+Left Back        |    Alt+Right Forward
F5 - Refresh"""
        shortcuts_text.insert("1.0", shortcuts)
        shortcuts_text.configure(state="disabled")

        ttk.Label(root, text="Font", style="Section.TLabel").pack(anchor="w")
        self.font_var = tk.StringVar(value=self.app.settings.get("reader_font", "Georgia"))
        font_names = sorted(set(tkfont.families()))
        self.font_combo = ttk.Combobox(root, textvariable=self.font_var, values=font_names, state="readonly")
        self.font_combo.pack(fill="x", pady=(4, 10))

        ttk.Label(root, text="Font Size", style="Section.TLabel").pack(anchor="w")
        self.size_var = tk.IntVar(value=int(self.app.settings.get("reader_font_size", 13)))
        size_row = ttk.Frame(root)
        size_row.pack(fill="x", pady=(4, 12))
        ttk.Spinbox(size_row, from_=9, to=28, textvariable=self.size_var, width=8).pack(side="left")
        ttk.Button(size_row, text="Apply Font", command=self.apply_font).pack(side="left", padx=(8, 0))

        ttk.Button(root, text="Close", command=self.destroy, style="Primary.TButton").pack(fill="x", pady=(8, 0))

    def pick_color(self, key):
        current = self.app.settings.get(key, "#ffffff")
        _rgb, color = colorchooser.askcolor(initialcolor=current, parent=self)
        if not color:
            return
        self.app.settings[key] = color
        self.app.save_settings()

    def apply_font(self):
        self.app.settings["reader_font"] = self.font_var.get() or "Georgia"
        self.app.settings["reader_font_size"] = int(self.size_var.get())
        self.app.save_settings()
