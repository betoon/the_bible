"""Helpers for configurable popup window sizes."""

from bible_app.config.settings import APP_SETTINGS


def configure_window_size(window, key, default_geometry, default_minsize=None):
    """Apply configured geometry and minimum size to a Tk/Toplevel window."""
    window.geometry(APP_SETTINGS.get_window_geometry(key, default_geometry))
    if default_minsize:
        min_geometry = f"{default_minsize[0]}x{default_minsize[1]}"
        window.minsize(*APP_SETTINGS.get_window_minsize(key, min_geometry))
