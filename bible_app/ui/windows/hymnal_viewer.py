"""Hymnal reader popup window."""

from datetime import datetime
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from bible_app.core.hymns import hymnal_files, load_hymnal_index, render_pdf_page_image
from bible_app.core.references import is_range_reference
from bible_app.storage.user_data import write_study_sessions
from bible_app.ui.window_config import configure_window_size
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class HymnalViewerWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.files = hymnal_files()
        self.filtered_hymns = []
        self.current_path = None
        self.load_token = 0
        self.loading = False
        self.sheet_zoom = 1.35
        self.sheet_photo = None
        self.selected_hymn = None
        if not hasattr(self.app, "hymnal_index_cache"):
            self.app.hymnal_index_cache = {}
        self.title("Hymnal Reader")
        configure_window_size(self, "hymnal_viewer", "980x720", (780, 540))
        self.build_ui()
        if self.files:
            self.hymnal_var.set(self.files[0].name)
            self.after(100, self.load_selected_hymnal)
        else:
            self.status_var.set("No PDF hymnals were found in data/hymnals.")

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Hymnal Reader", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Choose a hymnal, then pick a hymn from the left menu.", style="Muted.TLabel").pack(anchor="w", pady=(4, 10))

        top = ttk.Frame(root)
        top.pack(fill="x", pady=(0, 10))
        self.hymnal_var = tk.StringVar()
        self.hymnal_combo = ttk.Combobox(top, textvariable=self.hymnal_var, values=[path.name for path in self.files], state="readonly")
        self.hymnal_combo.pack(side="left", fill="x", expand=True)
        self.hymnal_combo.bind("<<ComboboxSelected>>", lambda _event: self.load_selected_hymnal())
        ttk.Button(top, text="Open PDF", command=self.open_current_pdf).pack(side="left", padx=(8, 0))

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Favorite", command=self.favorite_selected_hymn).pack(side="left")
        ttk.Button(actions, text="Link to Current Passage", command=self.link_selected_hymn).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Add to Session", command=self.add_selected_hymn_to_session).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Recent", command=self.show_recent_hymns).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Favorites", command=self.show_favorite_hymns).pack(side="left", padx=(6, 0))

        body = ttk.PanedWindow(root, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, padding=(0, 0, 10, 0))
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)

        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        search = ttk.Entry(search_row, textvariable=self.search_var)
        search.pack(side="left", fill="x", expand=True)
        search.bind("<KeyRelease>", lambda _event: self.refresh_hymn_list())
        ttk.Button(search_row, text="Clear", command=self.clear_search).pack(side="left", padx=(6, 0))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True)
        list_scroll = tk.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")
        self.hymn_list = tk.Listbox(list_frame, exportselection=False, yscrollcommand=list_scroll.set)
        self.hymn_list.pack(side="left", fill="both", expand=True)
        self.hymn_list.bind("<<ListboxSelect>>", self.on_hymn_selected)
        list_scroll.config(command=self.hymn_list.yview)

        self.status_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.status_var, style="Muted.TLabel", wraplength=260).pack(anchor="w", pady=(8, 0))

        self.title_var = tk.StringVar(value="Select a hymn")
        ttk.Label(right, textvariable=self.title_var, style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        view_buttons = ttk.Frame(right)
        view_buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(view_buttons, text="Zoom In", command=lambda: self.change_sheet_zoom(0.15)).pack(side="left")
        ttk.Button(view_buttons, text="Zoom Out", command=lambda: self.change_sheet_zoom(-0.15)).pack(side="left", padx=(6, 0))
        ttk.Button(view_buttons, text="Fit Width", command=self.fit_sheet_width).pack(side="left", padx=(6, 0))

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)
        sheet_tab = ttk.Frame(tabs, padding=4)
        text_tab = ttk.Frame(tabs, padding=4)
        tabs.add(sheet_tab, text="Sheet Music")
        tabs.add(text_tab, text="Text")

        sheet_frame = ttk.Frame(sheet_tab)
        sheet_frame.pack(fill="both", expand=True)
        sheet_y = tk.Scrollbar(sheet_frame)
        sheet_y.pack(side="right", fill="y")
        sheet_x = tk.Scrollbar(sheet_frame, orient="horizontal")
        sheet_x.pack(side="bottom", fill="x")
        self.sheet_canvas = tk.Canvas(sheet_frame, bg="#777777", highlightthickness=0, yscrollcommand=sheet_y.set, xscrollcommand=sheet_x.set)
        self.sheet_canvas.pack(side="left", fill="both", expand=True)
        sheet_y.config(command=self.sheet_canvas.yview)
        sheet_x.config(command=self.sheet_canvas.xview)
        self.sheet_canvas.bind("<MouseWheel>", self.on_sheet_mousewheel)

        text_frame = ttk.Frame(text_tab)
        text_frame.pack(fill="both", expand=True)
        text_scroll = tk.Scrollbar(text_frame)
        text_scroll.pack(side="right", fill="y")
        self.reader = tk.Text(text_frame, wrap="word", yscrollcommand=text_scroll.set, font=("Georgia", 12), padx=12, pady=10)
        self.reader.pack(side="left", fill="both", expand=True)
        self.reader.configure(state="disabled")
        text_scroll.config(command=self.reader.yview)

    def selected_hymnal_path(self):
        name = self.hymnal_var.get()
        for path in self.files:
            if path.name == name:
                return path
        return None

    def load_selected_hymnal(self):
        path = self.selected_hymnal_path()
        if not path:
            return
        self.current_path = path
        self.load_token += 1
        token = self.load_token
        cache_key = str(path.resolve())
        self.status_var.set("Reading hymnal index...")
        self.loading = True
        self.filtered_hymns = []
        self.hymn_list.delete(0, "end")
        self.hymn_list.insert("end", "Loading hymns...")
        self.show_reader_message("Loading hymnal index. The reader will fill in when it is ready.")
        if cache_key in self.app.hymnal_index_cache:
            self.finish_hymnal_load(token, path, self.app.hymnal_index_cache[cache_key])
            return
        runner = getattr(self.app, "background", None)
        if runner:
            runner.submit(
                lambda: self.load_hymnal_task(token, path, cache_key),
                on_success=lambda result: self.finish_hymnal_load(*result),
                on_error=lambda error: self.fail_hymnal_load(token, error),
            )
        else:
            threading.Thread(target=self.load_hymnal_worker, args=(token, path, cache_key), daemon=True).start()

    def load_hymnal_task(self, token, path, cache_key):
        hymns, from_cache = load_hymnal_index(path)
        self.app.hymnal_index_cache[cache_key] = hymns
        return token, path, hymns, from_cache

    def load_hymnal_worker(self, token, path, cache_key):
        try:
            result = self.load_hymnal_task(token, path, cache_key)
            self.after(0, lambda: self.finish_hymnal_load(*result))
        except Exception as exc:
            logger.exception("Could not load hymnal index for %s", path)
            self.after(0, lambda: self.fail_hymnal_load(token, exc))

    def finish_hymnal_load(self, token, path, hymns, from_cache=False):
        if token != self.load_token or path != self.current_path:
            return
        self.loading = False
        self.filtered_hymns = list(hymns)
        self.refresh_hymn_list()
        source = "saved index" if from_cache else "PDF scan"
        self.status_var.set(f"{len(hymns)} hymns available ({source}).")
        if hymns:
            self.hymn_list.selection_clear(0, "end")
            self.hymn_list.selection_set(0)
            self.hymn_list.activate(0)
            self.on_hymn_selected()
        else:
            self.show_reader_message("No individual hymn pages could be found in this PDF. You can still open the original PDF.")

    def fail_hymnal_load(self, token, error):
        if token != self.load_token:
            return
        self.loading = False
        self.filtered_hymns = []
        self.hymn_list.delete(0, "end")
        self.hymn_list.insert("end", "Could not read this hymnal.")
        self.status_var.set("Could not read hymnal.")
        self.show_reader_message(f"Could not read this hymnal.\n\n{error}")

    def refresh_hymn_list(self):
        if self.loading:
            return
        query = self.search_var.get().strip().lower()
        all_hymns = self.app.hymnal_index_cache.get(str(self.current_path.resolve()), []) if self.current_path else []
        if query:
            self.filtered_hymns = [
                hymn for hymn in all_hymns
                if query in hymn["title"].lower() or query in hymn["section"].lower() or query in str(hymn["number"])
            ]
        else:
            self.filtered_hymns = list(all_hymns)
        self.hymn_list.delete(0, "end")
        for hymn in self.filtered_hymns:
            self.hymn_list.insert("end", f'{hymn["number"]}. {hymn["title"]}')
        if not self.filtered_hymns:
            self.hymn_list.insert("end", "No hymns match that search.")
        self.status_var.set(f"{len(self.filtered_hymns)} hymns shown.")

    def clear_search(self):
        self.search_var.set("")
        self.refresh_hymn_list()

    def on_hymn_selected(self, _event=None):
        if not self.hymn_list.curselection() or not self.filtered_hymns:
            return
        index = self.hymn_list.curselection()[0]
        if index >= len(self.filtered_hymns):
            return
        hymn = self.filtered_hymns[index]
        self.selected_hymn = hymn
        self.app.remember_recent_hymn(hymn, self.current_path.name if self.current_path else "")
        self.title_var.set(f'{hymn["number"]}. {hymn["title"]} - {hymn["section"]} (page {hymn["page"]})')
        self.show_sheet_music(hymn)
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        self.reader.insert("1.0", hymn["text"])
        self.reader.configure(state="disabled")
        self.reader.yview_moveto(0)

    def show_reader_message(self, message):
        self.title_var.set("Hymnal Reader")
        self.sheet_photo = None
        self.sheet_canvas.delete("all")
        self.sheet_canvas.create_text(20, 20, text=message, anchor="nw", fill="white", width=620, font=("Segoe UI", 11))
        self.sheet_canvas.configure(scrollregion=self.sheet_canvas.bbox("all"))
        self.reader.configure(state="normal")
        self.reader.delete("1.0", "end")
        self.reader.insert("1.0", message)
        self.reader.configure(state="disabled")
        self.reader.yview_moveto(0)

    def show_sheet_music(self, hymn):
        if not self.current_path:
            self.show_reader_message("No hymnal PDF is selected.")
            return
        try:
            from PIL import ImageTk

            image = render_pdf_page_image(self.current_path, hymn["page"], self.sheet_zoom)
            self.sheet_photo = ImageTk.PhotoImage(image)
            self.sheet_canvas.delete("all")
            self.sheet_canvas.create_image(12, 12, image=self.sheet_photo, anchor="nw")
            self.sheet_canvas.configure(scrollregion=(0, 0, image.width + 24, image.height + 24))
            self.sheet_canvas.xview_moveto(0)
            self.sheet_canvas.yview_moveto(0)
        except Exception as exc:
            logger.exception("Could not render hymnal sheet music page %s from %s", hymn.get("page"), self.current_path)
            self.sheet_photo = None
            self.sheet_canvas.delete("all")
            message = f"Could not render the sheet music page.\n\n{exc}\n\nUse Open PDF to view the original hymnal."
            self.sheet_canvas.create_text(20, 20, text=message, anchor="nw", fill="white", width=620, font=("Segoe UI", 11))
            self.sheet_canvas.configure(scrollregion=self.sheet_canvas.bbox("all"))

    def change_sheet_zoom(self, delta):
        self.sheet_zoom = min(2.5, max(0.65, self.sheet_zoom + delta))
        if self.selected_hymn:
            self.show_sheet_music(self.selected_hymn)

    def fit_sheet_width(self):
        if not self.selected_hymn or not self.current_path:
            return
        try:
            from PIL import ImageTk

            image = render_pdf_page_image(self.current_path, self.selected_hymn["page"], 1.0)
            width = max(300, self.sheet_canvas.winfo_width() - 36)
            self.sheet_zoom = min(2.5, max(0.65, width / max(1, image.width)))
            image = render_pdf_page_image(self.current_path, self.selected_hymn["page"], self.sheet_zoom)
            self.sheet_photo = ImageTk.PhotoImage(image)
            self.sheet_canvas.delete("all")
            self.sheet_canvas.create_image(12, 12, image=self.sheet_photo, anchor="nw")
            self.sheet_canvas.configure(scrollregion=(0, 0, image.width + 24, image.height + 24))
            self.sheet_canvas.xview_moveto(0)
            self.sheet_canvas.yview_moveto(0)
        except Exception as exc:
            logger.exception("Could not fit hymnal sheet music page %s from %s", self.selected_hymn.get("page"), self.current_path)
            self.show_reader_message(f"Could not fit the sheet music page.\n\n{exc}")

    def on_sheet_mousewheel(self, event):
        self.sheet_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def open_current_pdf(self):
        path = self.current_path or self.selected_hymnal_path()
        if not path or not path.exists():
            messagebox.showinfo("Open Hymnal", "No local hymnal PDF is available.")
            return
        try:
            os.startfile(str(path))
        except Exception as exc:
            logger.exception("Could not open hymnal PDF: %s", path)
            messagebox.showerror("Open Hymnal", f"Could not open the hymnal PDF:\n{exc}")

    def current_hymn_or_none(self):
        if self.selected_hymn:
            return self.selected_hymn
        if self.hymn_list.curselection() and self.filtered_hymns:
            index = self.hymn_list.curselection()[0]
            if index < len(self.filtered_hymns):
                return self.filtered_hymns[index]
        return None

    def favorite_selected_hymn(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        message = self.app.toggle_hymn_favorite(hymn, self.current_path.name if self.current_path else "")
        self.status_var.set(message)

    def link_selected_hymn(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        message = self.app.link_hymn_to_reference(self.app.selected_ref, hymn, self.current_path.name if self.current_path else "")
        self.status_var.set(message)
        self.app.render_related_hymns(self.app.selected_ref)
        if not is_range_reference(self.app.selected_ref):
            self.app.render_chapter()

    def add_selected_hymn_to_session(self):
        hymn = self.current_hymn_or_none()
        if not hymn:
            return
        if not self.app.study_sessions:
            self.app.study_sessions.append({
                "name": "Hymn Study",
                "created": datetime.now().isoformat(timespec="seconds"),
                "references": [],
                "notes": "",
                "hymns": [],
                "documents": [],
            })
        session = self.app.study_sessions[0]
        session.setdefault("hymns", [])
        item = {
            "title": hymn.get("title", ""),
            "hymnal": self.current_path.name if self.current_path else "",
            "number": str(hymn.get("number", "")),
            "page": int(hymn.get("page", 0) or 0),
        }
        if item not in session["hymns"]:
            session["hymns"].append(item)
        write_study_sessions(self.app.study_sessions)
        self.status_var.set(f"Added hymn to session: {session.get('name', '')}")

    def show_recent_hymns(self):
        self.show_hymn_collection("Recent Hymns", self.app.recent_hymns)

    def show_favorite_hymns(self):
        self.show_hymn_collection("Favorite Hymns", self.app.hymn_favorites)

    def show_hymn_collection(self, title, items):
        window = tk.Toplevel(self)
        window.title(title)
        configure_window_size(window, "hymn_list", "520x420", (420, 320))
        root = ttk.Frame(window, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=title, style="Title.TLabel").pack(anchor="w")
        listing = tk.Listbox(root, exportselection=False)
        listing.pack(fill="both", expand=True, pady=(10, 0))
        for item in items:
            number = f"{item.get('number')}. " if item.get("number") else ""
            listing.insert("end", f"{number}{item.get('title', '')} ({item.get('hymnal', '')})")
        if not items:
            listing.insert("end", "Nothing saved yet.")
