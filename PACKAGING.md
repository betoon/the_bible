# Bible Reference Study Tool - Packaging Guide

This guide explains how to build and distribute the desktop app on Windows.

## Recommended Release Build

Run:

```text
build_release.bat
```

The older shortcut still works:

```text
build.bat
```

It simply calls `build_release.bat`.

## What The Release Build Does

The release script:

1. Checks Python files with `compileall`.
2. Runs the module test suite.
3. Installs build dependencies from `requirements-dev.txt` if PyInstaller is missing.
4. Removes the old executable and zip output.
5. Builds the app with `Bible_Reference_Study_Tool.spec`.
6. Creates a zip package in `dist`.

Expected outputs:

```text
dist\Bible_Reference_Study_Tool.exe
dist\Bible_Reference_Study_Tool.zip
```

## Included Resources

The PyInstaller specs include:

- `README.md`
- `USER_GUIDE.md`
- `REFERENCE_GUIDE.md`
- `DEVELOPERS_GUIDE.md`
- `bible_app\config\settings.ini`
- `study_data`
- `maps`
- `data\EN-English`
- `data\hymnals`
- `data\maps`
- `data\people`
- `data\NIV-Bible.pdf`
- `data\readme.txt`

If a new required folder or file is added to the app, add it to both:

```text
Bible_Reference_Study_Tool.spec
bible_reference_app.spec
```

## Installing For Development

Install runtime dependencies:

```text
python -m pip install -r requirements.txt
```

Install development and build dependencies:

```text
python -m pip install -r requirements-dev.txt
```

Editable install:

```text
python -m pip install -e .
```

After editable install, this command is available:

```text
bible-app
```

## Python Package Metadata

Package metadata lives in:

```text
setup.py
```

Version metadata lives in:

```text
bible_app\__init__.py
```

Update this before a release:

```python
__version__ = "1.0.0"
```

## Source Distribution

To build Python package artifacts:

```text
python -m pip install -r requirements-dev.txt
python -m build
```

Outputs appear in:

```text
dist
```

The source distribution uses:

```text
MANIFEST.in
```

## Debug Folder Build

The file:

```text
bible_reference_app.spec
```

builds a folder-style console version. This can be useful when diagnosing missing files or hidden imports.

Run:

```text
python -m PyInstaller --clean --noconfirm bible_reference_app.spec
```

## One-File Release Build

The file:

```text
Bible_Reference_Study_Tool.spec
```

builds the normal one-file windowed executable.

Run:

```text
python -m PyInstaller --clean --noconfirm Bible_Reference_Study_Tool.spec
```

## Smoke Test Checklist

After building, open:

```text
dist\Bible_Reference_Study_Tool.exe
```

Check:

- App starts without a console crash.
- Help > Open Help works.
- Help guide buttons open the bundled guide files.
- KJV sample opens.
- Search works.
- Personal note save works.
- Library Manager opens.
- Hymnal Reader opens.
- A hymnal sheet page renders if PDF rendering libraries bundled correctly.
- Settings window opens.
- App closes normally.

## Distribution Notes

The one-file executable stores user data outside the install folder:

```text
%LOCALAPPDATA%\BibleReferenceStudyTool
```

This means user notes and downloads survive app updates.

For a simple manual release, share:

```text
dist\Bible_Reference_Study_Tool.zip
```

For a formal Windows installer later, consider:

- Inno Setup
- NSIS
- WiX Toolset

An installer is not required for the current release flow.
