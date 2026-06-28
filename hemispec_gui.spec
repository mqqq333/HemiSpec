# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('hemispec')
# Keep the default GUI build lightweight. This collects package-owned data
# under src/hemispec only; it does not bundle repository-level local assets/.
# Release model/atlas bundles separately, or copy an approved asset bundle next to
# the compiled folder with ASSET_MANIFEST.md.

a = Analysis(
    ['scripts/hemispec_gui_entry.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'joblib',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'openpyxl.workbook',
        'sklearn.impute',
        'sklearn.linear_model',
        'sklearn.pipeline',
        'sklearn.preprocessing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='hemispec_gui',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='hemispec_gui',
)
