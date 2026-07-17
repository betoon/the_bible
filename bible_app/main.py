"""Application entry point.

During the refactor, the existing Tk application remains in
``bible_reference_app.py``. This module gives the new package a stable launch
point while windows and services are moved over in phases.
"""

from bible_reference_app import BibleReferenceApp


def main():
    BibleReferenceApp().mainloop()


if __name__ == "__main__":
    main()

