# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para o Sistema TI Papanduva
Gera um unico .exe com todas as dependencias embutidas.
"""

import sys
import os

# Caminho raiz do customtkinter (necessario para incluir os assets de tema)
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Inclui todos os arquivos de tema/assets do customtkinter
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=[
        'customtkinter',
        'darkdetect',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'sqlite3',
        'packaging',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='TI_Papanduva',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX pode causar falsos positivos em antivírus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # Sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # Coloque 'icone.ico' aqui se tiver um ícone
)
