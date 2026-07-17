# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bible_reference_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('USER_GUIDE.md', '.'),
        ('REFERENCE_GUIDE.md', '.'),
        ('DEVELOPERS_GUIDE.md', '.'),
        ('PACKAGING.md', '.'),
        ('bible_app\\config\\settings.ini', 'bible_app\\config'),
        ('study_data', 'study_data'),
        ('maps', 'maps'),
        ('data\\EN-English', 'data\\EN-English'),
        ('data\\hymnals', 'data\\hymnals'),
        ('data\\maps', 'data\\maps'),
        ('data\\people', 'data\\people'),
        ('data\\NIV-Bible.pdf', 'data'),
        ('data\\readme.txt', 'data'),
    ],
    hiddenimports=['pypdf', 'PyPDF2', 'pypdfium2', 'fitz', 'PIL', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Bible_Reference_Study_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
