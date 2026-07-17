"""Library manager and document viewer windows."""

import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from bible_app.config.constants import (
    BOOK_CHAPTERS,
    BOOK_ORDER,
    NEW_TESTAMENT_BOOKS,
    PROPHETS_BOOKS,
    TANAKH_BOOKS,
    TORAH_BOOKS,
    WRITINGS_BOOKS,
)
from bible_app.core.documents import convert_document_to_library_item
from bible_app.ui.window_config import configure_window_size
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class LibraryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.filtered_documents = []
        self.title("Library Manager")
        configure_window_size(self, "library_manager", "720x620", (600, 480))
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Library Manager", style="Title.TLabel").pack(anchor="w")

        self.summary_var = tk.StringVar()
        ttk.Label(root, textvariable=self.summary_var, style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(4, 12))

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(buttons, text="Download Current Book", command=self.download_current_book).pack(side="left", fill="x", expand=True)
        ttk.Button(buttons, text="Download New Testament", command=self.download_new_testament).pack(side="left", fill="x", expand=True, padx=(6, 0))

        tanakh_buttons = ttk.Frame(root)
        tanakh_buttons.pack(fill="x", pady=(0, 6))
        ttk.Button(tanakh_buttons, text="Download Old Testament / Hebrew Bible", command=self.download_tanakh).pack(side="left", fill="x", expand=True)
        ttk.Button(tanakh_buttons, text="Download Torah", command=self.download_torah).pack(side="left", fill="x", expand=True, padx=(6, 0))

        tanakh_buttons_2 = ttk.Frame(root)
        tanakh_buttons_2.pack(fill="x", pady=(0, 10))
        ttk.Button(tanakh_buttons_2, text="Download Prophets", command=self.download_prophets).pack(side="left", fill="x", expand=True)
        ttk.Button(tanakh_buttons_2, text="Download Writings", command=self.download_writings).pack(side="left", fill="x", expand=True, padx=(6, 0))

        doc_buttons = ttk.Frame(root)
        doc_buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(doc_buttons, text="Convert Document", command=self.convert_document).pack(side="left", fill="x", expand=True)
        ttk.Button(doc_buttons, text="View Selected Document", command=self.view_selected_document).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(doc_buttons, text="Open Original", command=self.open_selected_document_source).pack(side="left", fill="x", expand=True, padx=(6, 0))
        ttk.Button(root, text="Clear KJV Cache", command=self.clear_cache).pack(fill="x", pady=(0, 10))

        ttk.Label(root, text="Cached Chapters", style="Section.TLabel").pack(anchor="w")
        self.chapter_list = tk.Listbox(root, height=10, exportselection=False)
        self.chapter_list.pack(fill="both", expand=True, pady=(4, 10))

        ttk.Label(root, text="Converted Documents", style="Section.TLabel").pack(anchor="w")
        document_search = ttk.Frame(root)
        document_search.pack(fill="x", pady=(4, 4))
        self.document_search_var = tk.StringVar()
        document_search_entry = ttk.Entry(document_search, textvariable=self.document_search_var)
        document_search_entry.pack(side="left", fill="x", expand=True)
        document_search_entry.bind("<Return>", lambda _event: self.refresh_documents())
        ttk.Button(document_search, text="Search", command=self.refresh_documents).pack(side="left", padx=(6, 0))
        ttk.Button(document_search, text="Clear", command=self.clear_document_search).pack(side="left", padx=(6, 0))

        self.document_list = tk.Listbox(root, height=6, exportselection=False)
        self.document_list.pack(fill="both", expand=True, pady=(4, 0))
        self.document_list.bind("<<ListboxSelect>>", lambda _event: self.view_selected_document())

    def refresh(self):
        kjv_cached = self.app.cached_chapter_count(translation="KJV")
        jps_cached = self.app.cached_chapter_count(translation="JPS1917")
        total_all = sum(BOOK_CHAPTERS.values())
        total_tanakh = sum(BOOK_CHAPTERS[book] for book in TANAKH_BOOKS)
        self.summary_var.set(
            f"KJV cached: {kjv_cached}/{total_all}. JPS 1917 Tanakh cached: {jps_cached}/{total_tanakh}. "
            f"Converted documents: {len(self.app.library_documents)}. "
            "Missing KJV/JPS chapters can still be opened online and saved as you use them."
        )

        self.chapter_list.delete(0, "end")
        for book in BOOK_ORDER:
            cached_book = self.app.cached_chapter_count(book, "KJV")
            total_book = BOOK_CHAPTERS[book]
            jps_text = ""
            if book in TANAKH_BOOKS:
                jps_cached_book = self.app.cached_chapter_count(book, "JPS1917")
                jps_text = f" | JPS1917 {jps_cached_book}/{total_book}"
            self.chapter_list.insert("end", f"{book}: KJV {cached_book}/{total_book}{jps_text}")
        self.refresh_documents()

    def refresh_documents(self):
        query = self.document_search_var.get().strip().lower() if hasattr(self, "document_search_var") else ""
        if query:
            self.filtered_documents = [
                item for item in self.app.library_documents
                if query in item.get("title", "").lower() or query in item.get("text", "").lower()
            ]
        else:
            self.filtered_documents = list(self.app.library_documents)
        self.document_list.delete(0, "end")
        for item in self.filtered_documents:
            self.document_list.insert("end", f"{item.get('title', '')} ({item.get('type', '')})")

    def clear_document_search(self):
        self.document_search_var.set("")
        self.refresh_documents()

    def download_current_book(self):
        self.app.start_chapter_batch_download([self.app.current_book], self.app.current_book)
        self.after(1500, self.refresh)

    def download_new_testament(self):
        self.app.start_chapter_batch_download(NEW_TESTAMENT_BOOKS, "New Testament", "KJV")
        self.after(1500, self.refresh)

    def download_tanakh(self):
        self.app.start_chapter_batch_download(TANAKH_BOOKS, "Old Testament / Hebrew Bible", "JPS1917")
        self.after(1500, self.refresh)

    def download_torah(self):
        self.app.start_chapter_batch_download(TORAH_BOOKS, "Torah", "JPS1917")
        self.after(1500, self.refresh)

    def download_prophets(self):
        self.app.start_chapter_batch_download(PROPHETS_BOOKS, "Prophets", "JPS1917")
        self.after(1500, self.refresh)

    def download_writings(self):
        self.app.start_chapter_batch_download(WRITINGS_BOOKS, "Writings", "JPS1917")
        self.after(1500, self.refresh)

    def clear_cache(self):
        self.app.clear_kjv_cache()
        self.refresh()

    def convert_document(self):
        DocumentConversionWindow(self.app, on_close=self.refresh)

    def view_selected_document(self):
        if not self.document_list.curselection():
            return
        index = self.document_list.curselection()[0]
        if index < len(self.filtered_documents):
            DocumentViewerWindow(self.app, self.filtered_documents[index])

    def open_selected_document_source(self):
        if not self.document_list.curselection():
            return
        index = self.document_list.curselection()[0]
        if index >= len(self.filtered_documents):
            return
        source_path = self.filtered_documents[index].get("source_path", "")
        if not source_path or not Path(source_path).exists():
            messagebox.showinfo("Open Original", "No local source file is available for this document.")
            return
        try:
            os.startfile(source_path)
        except Exception as exc:
            logger.exception("Could not open document source file: %s", source_path)
            messagebox.showerror("Open Original", f"Could not open the source file:\n{exc}")


class DocumentConversionWindow(tk.Toplevel):
    def __init__(self, app, on_close=None):
        super().__init__(app)
        self.app = app
        self.on_close = on_close
        self.source_path = None
        self.title("Convert Document To Library")
        configure_window_size(self, "document_converter", "560x260", (480, 240))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Convert Document To Library", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Supported: PDF, DOCX, TXT, Markdown, HTML. Converted text is saved as JSON; extracted images are stored in the document images folder.",
            style="Muted.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(4, 12))

        self.file_var = tk.StringVar(value="No document selected")
        ttk.Label(root, textvariable=self.file_var, style="Muted.TLabel", wraplength=520).pack(anchor="w", pady=(0, 8))
        row = ttk.Frame(root)
        row.pack(fill="x", pady=(0, 10))
        ttk.Button(row, text="Choose Document", command=self.choose_document).pack(side="left")
        self.convert_button = ttk.Button(row, text="Convert", command=self.start_conversion, state="disabled", style="Primary.TButton")
        self.convert_button.pack(side="right")

        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=(4, 6))
        self.status_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w")

    def choose_document(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose Document",
            filetypes=[
                ("Readable documents", "*.pdf;*.docx;*.txt;*.md;*.html;*.htm"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Text files", "*.txt;*.md"),
                ("HTML files", "*.html;*.htm"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.source_path = path
        self.file_var.set(path)
        self.convert_button.configure(state="normal")

    def start_conversion(self):
        if not self.source_path:
            return
        title = simpledialog.askstring("Document Title", "Title for this library document:", initialvalue=Path(self.source_path).stem, parent=self)
        if not title:
            return
        self.convert_button.configure(state="disabled")
        self.status_var.set("Starting conversion...")
        runner = getattr(self.app, "background", None)
        if runner:
            runner.submit(
                lambda: self.convert_task(self.source_path, title),
                on_success=self.finish_conversion,
                on_error=self.fail_conversion,
            )
        else:
            threading.Thread(target=self.convert_worker, args=(self.source_path, title), daemon=True).start()

    def convert_task(self, path, title):
        return convert_document_to_library_item(
            path,
            title,
            progress=lambda value, message: self.after(0, lambda v=value, m=message: self.update_progress(v, m)),
        )

    def convert_worker(self, path, title):
        try:
            item = self.convert_task(path, title)
            self.after(0, lambda: self.finish_conversion(item))
        except Exception as exc:
            logger.exception("Document conversion failed for %s", path)
            self.after(0, lambda e=exc: self.fail_conversion(e))

    def update_progress(self, value, message):
        self.progress_var.set(value)
        self.status_var.set(message)

    def finish_conversion(self, item):
        self.progress_var.set(100)
        self.status_var.set("Conversion complete.")
        self.app.document_conversion_finished(item)
        if self.on_close:
            self.on_close()
        self.convert_button.configure(state="normal")

    def fail_conversion(self, error):
        self.convert_button.configure(state="normal")
        self.status_var.set("Conversion failed.")
        messagebox.showerror("Convert Document", str(error))


class DocumentViewerWindow(tk.Toplevel):
    def __init__(self, app, document):
        super().__init__(app)
        self.app = app
        self.document = document
        self.title(f"Library Document - {document.get('title', '')}")
        configure_window_size(self, "document_viewer", "900x700", (700, 520))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=self.document.get("title", "Untitled Document"), style="Title.TLabel").pack(anchor="w")
        meta = f"Type: {self.document.get('type', '')} | Images: {len(self.document.get('images', []))} | Source: {self.document.get('source_path', '')}"
        ttk.Label(root, text=meta, style="Muted.TLabel", wraplength=840).pack(anchor="w", pady=(4, 10))
        ttk.Button(root, text="Open Original File", command=self.open_source).pack(anchor="w", pady=(0, 8))

        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True)
        text_tab = ttk.Frame(tabs, padding=8)
        images_tab = ttk.Frame(tabs, padding=8)
        tabs.add(text_tab, text="Text")
        tabs.add(images_tab, text="Images")

        text_scroll = tk.Scrollbar(text_tab)
        text_scroll.pack(side="right", fill="y")
        text = tk.Text(text_tab, wrap="word", yscrollcommand=text_scroll.set)
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.document.get("text", "") or "No text was extracted from this document.")
        text.configure(state="disabled")
        text_scroll.config(command=text.yview)

        image_list = tk.Listbox(images_tab, exportselection=False)
        image_list.pack(fill="both", expand=True)
        for path in self.document.get("images", []):
            image_list.insert("end", path)
        if not self.document.get("images"):
            image_list.insert("end", "No images were extracted.")
        ttk.Button(images_tab, text="Open Selected Image", command=lambda: self.open_selected_image(image_list)).pack(fill="x", pady=(8, 0))

    def open_selected_image(self, image_list):
        if not image_list.curselection() or not self.document.get("images"):
            return
        path = self.document["images"][image_list.curselection()[0]]
        try:
            os.startfile(path)
        except Exception as exc:
            logger.exception("Could not open extracted document image: %s", path)
            messagebox.showerror("Open Image", f"Could not open image:\n{exc}")

    def open_source(self):
        source_path = self.document.get("source_path", "")
        if not source_path or not Path(source_path).exists():
            messagebox.showinfo("Open Original", "No local source file is available for this document.")
            return
        try:
            os.startfile(source_path)
        except Exception as exc:
            logger.exception("Could not open document source file: %s", source_path)
            messagebox.showerror("Open Original", f"Could not open the source file:\n{exc}")
