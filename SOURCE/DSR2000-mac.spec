# -*- mode: python ; coding: utf-8 -*-
# Spec para macOS (.app). El de Windows one-file es DSR2000.spec.


a = Analysis(
    ['DSR2000.py'],
    pathex=[],
    binaries=[],
    datas=[('files', 'files')],
    hiddenimports=['rtmidi', 'dearpygui', 'filedialpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DSR2000',
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
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DSR2000',
)
app = BUNDLE(
    coll,
    name='DSR2000.app',
    icon='icon.icns',
    bundle_identifier='com.carlobandini.dsr2000',
)
