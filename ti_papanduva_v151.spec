# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec - TI Papanduva v1.5.1 (Python 3.8.10 - compatível com Windows 7 SP1+)
Modo PASTA (onedir): menos falsos positivos de antivirus do que o arquivo unico.
"""

import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, 'customtkinter'), ('icone.ico', '.')],
    hiddenimports=['customtkinter', 'darkdetect', 'tkinter', 'tkinter.ttk',
                   'tkinter.messagebox', 'tkinter.filedialog', 'sqlite3', 'packaging'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

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
    icon='icone.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='TI_Papanduva',
)
