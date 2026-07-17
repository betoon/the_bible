"""Study dashboard popup window."""

import tkinter as tk
from tkinter import ttk

from bible_app.ui.window_config import configure_window_size


class StudyDashboardWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Study Dashboard")
        configure_window_size(self, "study_dashboard", "760x640", (640, 480))
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Dashboard", style="Title.TLabel").pack(anchor="w")

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(8, 10))
        ttk.Button(buttons, text="Continue", command=lambda: self.app.open_reference(self.app.selected_ref)).pack(side="left")
        ttk.Button(buttons, text="Worksheet", command=self.app.open_study_worksheet).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Search Everything", command=self.app.open_search_everything).pack(side="left", padx=(8, 0))

        text = tk.Text(root, wrap="word")
        text.pack(fill="both", expand=True)
        text.insert("1.0", "\n".join(self.dashboard_lines()))
        text.configure(state="disabled")

    def dashboard_lines(self):
        lines = [f"Current passage: {self.app.selected_ref}", "", "Reading Plans"]
        for plan in self.app.reading_plans[:4]:
            completed = set(plan.get("completed", []))
            next_ref = next((ref for ref in plan.get("references", []) if ref not in completed), "Complete")
            lines.append(f"- {plan.get('name', '')}: {next_ref} ({len(completed)}/{len(plan.get('references', []))})")

        lines.extend(["", "Recent Passages"])
        lines.extend(f"- {item.get('reference', '')}" for item in self.app.recent_references[:8])

        lines.extend(["", "Recent Notes"])
        lines.extend(f"- {ref}: {note[:90]}" for ref, note in list(self.app.notes.items())[-8:][::-1] if note)

        lines.extend(["", "Active Sessions"])
        lines.extend(f"- {session.get('name', '')}: {len(session.get('references', []))} passages, {len(session.get('hymns', []))} hymns" for session in self.app.study_sessions[:8])

        lines.extend(["", "Recent Hymns"])
        lines.extend(f"- {hymn.get('number', '')} {hymn.get('title', '')} ({hymn.get('hymnal', '')})" for hymn in self.app.recent_hymns[:8])
        return lines
