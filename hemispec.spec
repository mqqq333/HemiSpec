# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('hemispec')
# Keep the default CLI build lightweight. This collects package-owned data
# under src/hemispec only; it does not bundle repository-level local assets/.
# Release model/atlas bundles separately, or copy an approved asset bundle next to
# the compiled folder with ASSET_MANIFEST.md.

a = Analysis(
    ['scripts/hemispec_entry.py'],
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
    a.binaries,
    a.datas,
    [],
    name='hemispec',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
