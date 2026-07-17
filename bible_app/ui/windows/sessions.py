"""Study session and reading plan popup windows."""

from datetime import datetime
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from bible_app.config.paths import EXPORT_DIR
from bible_app.core.chapter_a_day import (
    CHAPTER_A_DAY_PLAN_NAME,
    chapter_a_day_entry_for_index,
    is_chapter_a_day_plan_name,
)
from bible_app.core.references import reference_parts
from bible_app.storage.user_data import write_reading_plans, write_study_sessions, write_worksheets
from bible_app.ui.window_config import configure_window_size


class StudySessionsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = None
        self.title("Study Sessions")
        configure_window_size(self, "study_sessions", "860x620", (700, 480))
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Session Workspace", style="Title.TLabel").pack(anchor="w")

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, pady=(10, 0))
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        self.session_list = tk.Listbox(left, exportselection=False)
        self.session_list.pack(fill="both", expand=True)
        self.session_list.bind("<<ListboxSelect>>", self.on_session_selected)
        ttk.Button(left, text="New Session", command=self.new_session).pack(fill="x", pady=(8, 0))
        ttk.Button(left, text="Add Current Passage", command=self.add_current).pack(fill="x", pady=(6, 0))

        self.refs_list = tk.Listbox(right, height=10, exportselection=False)
        self.refs_list.pack(fill="x")
        self.refs_list.bind("<<ListboxSelect>>", self.open_ref)
        ttk.Label(right, text="Session Notes", style="Section.TLabel").pack(anchor="w", pady=(10, 4))
        self.notes_text = tk.Text(right, height=10, wrap="word")
        self.notes_text.pack(fill="both", expand=True)

        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Save", command=self.save_current).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Export", command=self.export_current).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        self.session_list.delete(0, "end")
        for session in self.app.study_sessions:
            self.session_list.insert("end", f"{session['name']} ({len(session.get('references', []))})")
        if self.app.study_sessions and self.current_index is None:
            self.session_list.selection_set(0)
            self.on_session_selected()

    def new_session(self):
        name = simpledialog.askstring("Study Session", "Session name:", parent=self)
        if not name:
            return
        self.app.study_sessions.append({"name": name.strip(), "created": datetime.now().isoformat(timespec="seconds"), "references": [], "notes": ""})
        write_study_sessions(self.app.study_sessions)
        self.current_index = len(self.app.study_sessions) - 1
        self.refresh()

    def on_session_selected(self, _event=None):
        if not self.session_list.curselection():
            return
        self.current_index = self.session_list.curselection()[0]
        session = self.app.study_sessions[self.current_index]
        self.refs_list.delete(0, "end")
        for ref in session.get("references", []):
            self.refs_list.insert("end", f"{ref} - {self.app.passage_text(ref)[:70]}")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", session.get("notes", ""))

    def add_current(self):
        if self.current_index is None:
            self.new_session()
            if self.current_index is None:
                return
        session = self.app.study_sessions[self.current_index]
        if self.app.selected_ref not in session["references"]:
            session["references"].append(self.app.selected_ref)
        write_study_sessions(self.app.study_sessions)
        self.on_session_selected()
        self.refresh()

    def save_current(self):
        if self.current_index is None:
            return
        self.app.study_sessions[self.current_index]["notes"] = self.notes_text.get("1.0", "end").strip()
        write_study_sessions(self.app.study_sessions)

    def open_ref(self, _event=None):
        if self.current_index is None or not self.refs_list.curselection():
            return
        ref = self.app.study_sessions[self.current_index]["references"][self.refs_list.curselection()[0]]
        self.app.open_reference(ref)

    def export_current(self):
        if self.current_index is None:
            return
        self.save_current()
        session = self.app.study_sessions[self.current_index]
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", session["name"]).strip("-")
        path = EXPORT_DIR / f"study-session-{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [f"# {session['name']}", "", f"Created: {session.get('created', '')}", "", "## Passages", ""]
        for ref in session.get("references", []):
            lines.extend([f"### {ref}", "", self.app.passage_text(ref), ""])
        lines.extend(["## Notes", "", session.get("notes", "")])
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Export Complete", f"Exported to:\n{path}")


class ReadingPlansWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_index = 0
        self.title("Reading Plans")
        configure_window_size(self, "reading_plans", "780x580", (640, 440))
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Reading Plans", style="Title.TLabel").pack(anchor="w")
        self.plan_var = tk.StringVar()
        self.plan_combo = ttk.Combobox(root, textvariable=self.plan_var, state="readonly")
        self.plan_combo.pack(fill="x", pady=(10, 8))
        self.plan_combo.bind("<<ComboboxSelected>>", self.on_plan_selected)
        self.progress_var = tk.StringVar()
        ttk.Label(root, textvariable=self.progress_var, style="Muted.TLabel").pack(anchor="w")
        self.refs_list = tk.Listbox(root, exportselection=False)
        self.refs_list.pack(fill="both", expand=True, pady=(8, 8))
        self.refs_list.bind("<<ListboxSelect>>", self.open_selected)
        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Mark Complete", command=self.mark_complete).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Open Next", command=self.open_next).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(buttons, text="Open Worksheet", command=self.open_worksheet).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def refresh(self):
        self.plan_combo.configure(values=[plan["name"] for plan in self.app.reading_plans])
        if self.app.reading_plans:
            self.plan_var.set(self.app.reading_plans[self.current_index]["name"])
        self.render_refs()

    def current_plan(self):
        if not self.app.reading_plans:
            return None
        return self.app.reading_plans[self.current_index]

    def on_plan_selected(self, _event=None):
        for index, plan in enumerate(self.app.reading_plans):
            if plan["name"] == self.plan_var.get():
                self.current_index = index
                break
        self.render_refs()

    def render_refs(self):
        self.refs_list.delete(0, "end")
        plan = self.current_plan()
        if not plan:
            return
        completed = set(plan.get("completed", []))
        total = len(plan.get("references", []))
        done = len(completed)
        self.progress_var.set(f"{done}/{total} complete")
        for ref in plan.get("references", []):
            index = self.refs_list.size() + 1
            marker = "[x]" if self.completion_key(plan, index - 1, ref) in completed or ref in completed else "[ ]"
            prefix = f"Day {index}: " if is_chapter_a_day_plan_name(plan.get("name")) else ""
            self.refs_list.insert("end", f"{marker} {prefix}{ref}")

    def completion_key(self, plan, index, ref):
        if is_chapter_a_day_plan_name(plan.get("name")):
            return f"Day {index + 1}: {ref}"
        return ref

    def selected_index(self):
        if not self.refs_list.curselection():
            return None
        return self.refs_list.curselection()[0]

    def selected_ref(self):
        plan = self.current_plan()
        index = self.selected_index()
        if not plan or index is None:
            return None
        return plan["references"][index]

    def open_selected(self, _event=None):
        ref = self.selected_ref()
        if ref:
            self.app.open_reference(ref)

    def mark_complete(self):
        ref = self.selected_ref()
        plan = self.current_plan()
        index = self.selected_index()
        if not ref or not plan or index is None:
            return
        key = self.completion_key(plan, index, ref)
        if key not in plan["completed"]:
            plan["completed"].append(key)
        write_reading_plans(self.app.reading_plans)
        self.render_refs()

    def open_next(self):
        plan = self.current_plan()
        if not plan:
            return
        completed = set(plan.get("completed", []))
        for index, ref in enumerate(plan.get("references", [])):
            if self.completion_key(plan, index, ref) not in completed and ref not in completed:
                self.refs_list.selection_clear(0, "end")
                self.refs_list.selection_set(index)
                self.refs_list.see(index)
                self.app.open_reference(ref)
                return

    def open_worksheet(self):
        ref = self.selected_ref()
        plan = self.current_plan()
        index = self.selected_index()
        if not ref or not plan or index is None:
            return
        if is_chapter_a_day_plan_name(plan.get("name")):
            entry = chapter_a_day_entry_for_index(index) or {"day": index + 1, "reference": ref}
            ChapterADayWorksheetWindow(self.app, entry, self)
            return
        self.app.open_reference(ref)
        self.app.open_study_worksheet()

    def mark_ref_complete(self, ref, index=None):
        plan = self.current_plan()
        if not ref or not plan:
            return
        if index is None:
            index = self.selected_index()
        key = self.completion_key(plan, index or 0, ref)
        if key not in plan["completed"]:
            plan["completed"].append(key)
            write_reading_plans(self.app.reading_plans)
        self.render_refs()


class ChapterADayWorksheetWindow(tk.Toplevel):
    def __init__(self, app, entry, reading_window=None):
        super().__init__(app)
        self.app = app
        self.entry = entry
        self.reading_window = reading_window
        self.day = int(entry.get("day", 0) or 0)
        self.ref = str(entry.get("reference", "")).strip()
        self.index = max(0, self.day - 1)
        self.key = f"{CHAPTER_A_DAY_PLAN_NAME} Day {self.day}: {self.ref}"
        self.widgets = {}
        self.title(f"Chapter A Day - Day {self.day}")
        configure_window_size(self, "chapter_a_day", "980x760", (760, 560))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Day {self.day}: {self.ref}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="SOAP Journal", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        scripture_text = self.chapter_text()
        data = self.app.worksheets.get(self.key, {})
        self.add_field(left, "scripture", "Scripture", data.get("scripture") or scripture_text or "Open or download this chapter to fill the Scripture text.", height=26, expand=True)
        self.add_field(right, "observation", "Observation", data.get("observation", ""), height=7)
        self.add_field(right, "application", "Application", data.get("application", ""), height=7)
        self.add_field(right, "prayer", "Prayer", data.get("prayer", ""), height=7)

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Save", command=self.save, style="Primary.TButton").pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Save & Mark Complete", command=self.save_and_mark_complete).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(buttons, text="Open In Reader", command=lambda: self.app.open_reference(self.ref)).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def chapter_text(self):
        if hasattr(self.app, "chapter_text"):
            return self.app.chapter_text(self.ref)
        parts = reference_parts(self.ref)
        if not parts:
            return self.app.passage_text(self.ref)
        book, chapter, _verse = parts
        lines = []
        for item_ref, text in self.app.all_references():
            item_parts = reference_parts(item_ref)
            if item_parts and item_parts[0] == book and item_parts[1] == chapter:
                lines.append(f"{item_parts[2]}. {text}")
        return "\n\n".join(lines) or self.app.passage_text(self.ref)

    def add_field(self, parent, key, label, value, height=4, expand=False):
        ttk.Label(parent, text=label, style="Section.TLabel").pack(anchor="w", pady=(0 if not self.widgets else 8, 0))
        widget = tk.Text(parent, height=height, wrap="word")
        widget.pack(fill="both" if expand else "x", expand=expand, pady=(4, 0))
        widget.insert("1.0", value)
        self.widgets[key] = widget

    def worksheet_data(self):
        data = {key: widget.get("1.0", "end").strip() for key, widget in self.widgets.items()}
        data.setdefault("interpretation", "")
        data.setdefault("questions", "")
        data.setdefault("related_hymn", "")
        data.setdefault("tags", "Chapter A Day")
        data["updated"] = datetime.now().isoformat(timespec="seconds")
        return data

    def save(self):
        self.app.worksheets[self.key] = self.worksheet_data()
        write_worksheets(self.app.worksheets)
        try:
            self.app.render_chapter()
        except Exception:
            pass
        messagebox.showinfo("Chapter A Day", "Worksheet saved.")

    def save_and_mark_complete(self):
        self.app.worksheets[self.key] = self.worksheet_data()
        write_worksheets(self.app.worksheets)
        if self.reading_window:
            self.reading_window.mark_ref_complete(self.ref, self.index)
        messagebox.showinfo("Chapter A Day", "Worksheet saved and day marked complete.")


class StudyBinderWindow(tk.Toplevel):
    def __init__(self, app, maps_for_reference_func=None):
        super().__init__(app)
        self.app = app
        self.maps_for_reference = maps_for_reference_func or (lambda _ref: [])
        self.title("Study Session Binder")
        configure_window_size(self, "study_binder", "900x700", (740, 520))

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Study Session Binder", style="Title.TLabel").pack(anchor="w")

        self.session_var = tk.StringVar()
        self.session_combo = ttk.Combobox(
            root,
            textvariable=self.session_var,
            state="readonly",
            values=[session.get("name", "") for session in self.app.study_sessions],
        )
        self.session_combo.pack(fill="x", pady=(10, 8))
        self.session_combo.bind("<<ComboboxSelected>>", self.refresh)

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        self.views = {}
        for name in ("Passages", "Notes", "People", "Maps", "Hymns", "Documents", "Export"):
            frame = ttk.Frame(self.tabs, padding=8)
            self.tabs.add(frame, text=name)
            text = tk.Text(frame, wrap="word")
            text.pack(fill="both", expand=True)
            self.views[name] = text

        ttk.Button(root, text="Export Binder Markdown", command=self.export_binder).pack(fill="x", pady=(8, 0))
        if self.app.study_sessions:
            self.session_var.set(self.app.study_sessions[0].get("name", ""))
            self.refresh()

    def session(self):
        for session in self.app.study_sessions:
            if session.get("name") == self.session_var.get():
                return session
        return self.app.study_sessions[0] if self.app.study_sessions else None

    def set_view(self, name, text):
        widget = self.views[name]
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def refresh(self, _event=None):
        session = self.session()
        if not session:
            for name in self.views:
                self.set_view(name, "No study sessions yet.")
            return

        refs = session.get("references", [])
        self.set_view("Passages", "\n\n".join(f"{ref}\n{self.app.passage_text(ref)}" for ref in refs) or "No passages yet.")
        self.set_view("Notes", session.get("notes", "") or "No session notes yet.")
        people = sorted({person for ref in refs for person in self.app.people_for_reference(ref)})
        self.set_view("People", "\n".join(people) or "No people gathered yet.")
        maps = sorted({item.get("title", "") for ref in refs for item in self.maps_for_reference(ref)})
        self.set_view("Maps", "\n".join(maps) or "No maps gathered yet.")
        hymns = session.get("hymns", [])
        self.set_view("Hymns", "\n".join(f"{hymn.get('number', '')} {hymn.get('title', '')} ({hymn.get('hymnal', '')})" for hymn in hymns) or "No hymns added yet.")
        docs = session.get("documents", [])
        self.set_view("Documents", "\n".join(docs) or "No documents attached yet.")
        self.set_view("Export", "Use the export button below to save this binder as Markdown.")

    def export_binder(self):
        session = self.session()
        if not session:
            return
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", session.get("name", "binder")).strip("-")
        path = EXPORT_DIR / f"study-binder-{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        lines = [f"# {session.get('name', 'Study Binder')}", "", "## Passages", ""]
        for ref in session.get("references", []):
            lines.extend([f"### {ref}", self.app.passage_text(ref), ""])
        lines.extend(["## Notes", session.get("notes", ""), "", "## Hymns", ""])
        for hymn in session.get("hymns", []):
            lines.append(f"- {hymn.get('number', '')} {hymn.get('title', '')} ({hymn.get('hymnal', '')})")
        path.write_text("\n".join(lines), encoding="utf-8")
        messagebox.showinfo("Study Binder", f"Exported:\n{path}")
