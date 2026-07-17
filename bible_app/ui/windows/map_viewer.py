"""Map viewer popup window."""

import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from bible_app.core.maps import resolve_local_map_image
from bible_app.ui.window_config import configure_window_size
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class MapViewerWindow(tk.Toplevel):
    def __init__(self, app, map_item):
        super().__init__(app)
        self.app = app
        self.map_item = map_item
        self.image_ref = None
        self.original_image_path = resolve_local_map_image(self.map_item.get("local_image", ""))
        self.title(f"Map - {map_item.get('title', 'Map')}")
        configure_window_size(self, "map_viewer", "980x760", (720, 520))
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=self.map_item.get("title", "Map"), style="Title.TLabel").pack(anchor="w")
        meta = " | ".join(
            value for value in [
                self.map_item.get("period", ""),
                self.map_item.get("region", ""),
                self.map_item.get("license", ""),
            ]
            if value
        )
        if meta:
            ttk.Label(root, text=meta, style="Muted.TLabel", wraplength=920).pack(anchor="w", pady=(4, 8))
        if self.map_item.get("summary"):
            ttk.Label(root, text=self.map_item.get("summary"), style="Muted.TLabel", wraplength=920).pack(anchor="w", pady=(0, 8))
        ttk.Button(root, text="Open Image Externally", command=self.open_external).pack(anchor="w", pady=(0, 8))

        image_path = self.original_image_path
        if not image_path or not Path(image_path).exists():
            ttk.Label(root, text="No local image is available for this map entry.", style="Muted.TLabel").pack(anchor="w")
            return

        canvas_frame = ttk.Frame(root)
        canvas_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        v_scroll = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        try:
            image = self.load_display_image(image_path)
            self.image_ref = image
            canvas.create_image(0, 0, anchor="nw", image=self.image_ref)
            canvas.configure(scrollregion=(0, 0, image.width(), image.height()))
        except Exception as exc:
            logger.exception("Could not display map image inside app: %s", image_path)
            canvas.create_text(
                20,
                20,
                anchor="nw",
                text=f"Could not display the map image inside the app.\n\n{exc}\n\nUse Open Image Externally.",
                fill="#333333",
                width=700,
            )

    def load_display_image(self, image_path):
        max_width = 920
        max_height = 620
        try:
            from PIL import Image, ImageTk

            source = Image.open(image_path)
            source.thumbnail((max_width, max_height))
            return ImageTk.PhotoImage(source)
        except Exception as exc:
            logger.info("Pillow could not load map image %s; trying Tk PhotoImage. Error: %s", image_path, exc)
            image = tk.PhotoImage(file=image_path)
            factor = max(1, int(max(image.width() / max_width, image.height() / max_height)))
            if factor > 1:
                image = image.subsample(factor, factor)
            return image

    def open_external(self):
        if not self.original_image_path or not Path(self.original_image_path).exists():
            messagebox.showinfo("Map", "No local image is available for this map entry.")
            return
        try:
            os.startfile(self.original_image_path)
        except Exception as exc:
            logger.exception("Could not open map image externally: %s", self.original_image_path)
            messagebox.showerror("Open Map", f"Could not open image:\n{exc}")
