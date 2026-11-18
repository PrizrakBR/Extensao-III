# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec - TI Papanduva v1.2
Modo PASTA (onedir): menos falsos positivos de antivirus do que o arquivo unico.
"""

import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, 'customtkinter')],
    hiddenimports=['customtkinter', 'darkdetect', 'tkinter', 'tkinter.ttk',
                   'tkinter.messagebox', 'tkinter.filedialog', 'sqlite3', 'packaging'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TI_Papanduva',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='TI_Papanduva',
)
