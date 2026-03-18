# -*- mode: python ; coding: utf-8 -*-
# AcademiX.spec
# PyInstaller spec file - gives more control than command-line flags
#
# Usage:
#   pyinstaller AcademiX.spec
#
# Output: dist\AcademiX.exe

block_cipher = None

a = Analysis(
    ['academix.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('academix.ico', '.'),          # bundle the icon
    ],
    hiddenimports=[
        'tkcalendar',
        'babel.numbers',
        'babel.dates',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends._backend_tk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AcademiX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='academix.ico',     # taskbar + exe icon
    version_file=None,
)
