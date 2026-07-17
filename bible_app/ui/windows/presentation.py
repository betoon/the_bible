"""Clean presentation mode popup."""

import tkinter as tk

from bible_app.ui.window_config import configure_window_size


class PresentationWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(f"Presentation - {app.selected_ref}")
        configure_window_size(self, "presentation_mode", "1000x720", (800, 560))
        self.configure(bg="#111111")

        title = tk.Label(self, text=app.selected_ref, bg="#111111", fg="white", font=("Segoe UI", 26, "bold"))
        title.pack(anchor="w", padx=24, pady=(20, 8))

        body = tk.Text(
            self,
            wrap="word",
            bg="#111111",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Georgia", 20),
            padx=24,
            pady=16,
        )
        body.pack(fill="both", expand=True)

        lines = [app.passage_text(app.selected_ref), ""]
        note = app.notes.get(app.selected_ref, "")
        if note:
            lines.extend(["Notes:", note, ""])
        hymns = app.hymn_links.get(app.selected_ref, [])
        if hymns:
            lines.append("Related Hymns:")
            lines.extend(f"- {hymn.get('number', '')} {hymn.get('title', '')}" for hymn in hymns)

        body.insert("1.0", "\n".join(lines))
        body.configure(state="disabled")
        self.bind("<Escape>", lambda _event: self.destroy())
