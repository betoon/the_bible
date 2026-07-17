"""Shared UI style constants and helpers."""

from tkinter import ttk

from bible_app.config.settings import ACCENT, APP_BG, APP_PANEL, BORDER, TEXT, TEXT_SECONDARY


class AppTheme:
    bg = APP_BG
    panel = APP_PANEL
    accent = ACCENT
    text = TEXT
    muted = TEXT_SECONDARY
    border = BORDER
    button_bg = "#F4F6F8"
    button_hover = "#DDE7F3"
    button_pressed = "#C9DAEE"

    @staticmethod
    def configure_styles(root):
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=AppTheme.bg)
        style.configure("Panel.TFrame", background=AppTheme.panel)
        style.configure("Toolbar.TFrame", background=AppTheme.bg)
        style.configure("Status.TFrame", background=AppTheme.panel, relief="solid", borderwidth=1)

        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=AppTheme.text, background=AppTheme.panel)
        style.configure("Section.TLabel", font=("Segoe UI", 10, "bold"), foreground=AppTheme.text, background=AppTheme.panel)
        style.configure("Muted.TLabel", font=("Segoe UI", 9), foreground=AppTheme.muted, background=AppTheme.panel)
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground=AppTheme.muted, background=AppTheme.panel)
        style.configure("TLabel", font=("Segoe UI", 10), foreground=AppTheme.text, background=AppTheme.panel)

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="white",
            background=AppTheme.accent,
            borderwidth=1,
            relief="raised",
            padding=(12, 8),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#106EBE"), ("pressed", "#0D5AA0")],
            foreground=[("disabled", "#F1F1F1"), ("!disabled", "white")],
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            background=AppTheme.button_bg,
            foreground=AppTheme.text,
            borderwidth=1,
            relief="raised",
            padding=(10, 7),
        )
        style.map(
            "TButton",
            background=[("active", AppTheme.button_hover), ("pressed", AppTheme.button_pressed)],
            foreground=[("disabled", "#8A8A8A"), ("!disabled", AppTheme.text)],
        )

        style.configure(
            "Tool.TMenubutton",
            font=("Segoe UI", 10),
            background=AppTheme.button_bg,
            foreground=AppTheme.text,
            borderwidth=1,
            relief="raised",
            padding=(10, 7),
        )
        style.map("Tool.TMenubutton", background=[("active", AppTheme.button_hover), ("pressed", AppTheme.button_pressed)])

        style.configure(
            "TCombobox",
            fieldbackground=AppTheme.panel,
            background=AppTheme.panel,
            foreground=AppTheme.text,
            font=("Segoe UI", 10),
            padding=6,
        )
        root.configure(bg=AppTheme.bg)
        return style


def configure_app_styles(root):
    return AppTheme.configure_styles(root)
