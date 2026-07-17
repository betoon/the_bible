"""Cross-reference explorer and graph windows."""

import tkinter as tk
from tkinter import messagebox, ttk

from bible_app.core.references import normalized_reference
from bible_app.ui.window_config import configure_window_size


class CrossReferenceExplorerWindow(tk.Toplevel):
    def __init__(self, app, ref):
        super().__init__(app)
        self.app = app
        self.ref = normalized_reference(ref)
        self.targets = []
        self.title(f"Cross-Reference Explorer - {self.ref}")
        configure_window_size(self, "cross_reference_explorer", "760x620", (620, 460))

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Cross References: {self.ref}", style="Title.TLabel").pack(anchor="w")

        row = ttk.Frame(root)
        row.pack(fill="x", pady=(8, 10))
        self.target_var = tk.StringVar()
        self.reason_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.target_var, width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.reason_var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(row, text="Add Link", command=self.add_link).pack(side="left")

        self.listbox = tk.Listbox(root, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.open_selected)
        self.refresh()

    def refresh(self):
        self.targets = []
        self.listbox.delete(0, "end")
        for group, items in self.app.grouped_cross_references(self.ref).items():
            if not items:
                continue
            self.listbox.insert("end", f"== {group} ==")
            self.targets.append(None)
            for item in items:
                self.listbox.insert("end", f"{item['target']} - {item.get('reason', '')}")
                self.targets.append(item["target"])
        if not self.targets:
            self.listbox.insert("end", "No related references yet.")
            self.targets.append(None)

    def add_link(self):
        if self.app.add_user_cross_reference(self.ref, self.target_var.get(), self.reason_var.get()):
            self.target_var.set("")
            self.reason_var.set("")
            self.refresh()
        else:
            messagebox.showinfo("Cross Reference", "Use a target like John 1:1.")

    def open_selected(self, _event=None):
        if not self.listbox.curselection():
            return
        target = self.targets[self.listbox.curselection()[0]]
        if target:
            self.app.open_reference(target)


class CrossReferenceGraphWindow(tk.Toplevel):
    def __init__(self, app, edges_func):
        super().__init__(app)
        self.app = app
        self.title("Cross-Reference Graph")
        configure_window_size(self, "cross_reference_graph", "760x560", (620, 420))
        self.edges = edges_func(app.selected_ref)
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text=f"Cross-Reference Graph: {self.app.selected_ref}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Select a link to open the connected passage.", style="Muted.TLabel").pack(anchor="w", pady=(4, 10))
        self.link_list = tk.Listbox(root, exportselection=False)
        self.link_list.pack(fill="both", expand=True)
        self.link_list.bind("<<ListboxSelect>>", self.open_selected)
        if not self.edges:
            self.link_list.insert("end", "No cross-reference links available for this passage.")
            return
        for source, target in self.edges:
            self.link_list.insert("end", f"{source} -> {target}")

    def open_selected(self, _event=None):
        if not self.link_list.curselection() or not self.edges:
            return
        _source, target = self.edges[self.link_list.curselection()[0]]
        self.app.open_reference(target)
