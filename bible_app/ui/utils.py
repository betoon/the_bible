"""Small UI helpers shared by future window modules."""

import tkinter as tk


def set_text(widget, text):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    widget.configure(state="disabled")


def bind_mousewheel(widget, callback):
    widget.bind("<MouseWheel>", callback)
    widget.bind("<Button-4>", callback)
    widget.bind("<Button-5>", callback)

