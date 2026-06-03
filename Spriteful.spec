# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# psd-tools ships data files and C-extension deps (numpy) that the default
# import analysis can miss; collect everything so PSD import works in the bundle.
psd_datas, psd_binaries, psd_hiddenimports = collect_all('psd_tools')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=psd_binaries,
    datas=psd_datas + [('spriteful.ico', '.')],
    hiddenimports=psd_hiddenimports,
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
    name='Spriteful',
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
    icon='spriteful.ico',
)
