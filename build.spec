# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for PDF Editor.

Build with:
    pyinstaller build.spec

Produces a single-file executable in dist/PDFEditor (or dist/PDFEditor.exe
on Windows). customtkinter ships its own theme JSON assets, which are
collected automatically below so the packaged app doesn't fall back to
plain Tk styling.
"""

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

datas = []
datas += collect_data_files("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "pandas", "numpy",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "gi", "IPython", "notebook", "pytest",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="PDFEditor",
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
    icon=None,
)
