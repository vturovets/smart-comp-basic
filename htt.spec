# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['cli.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.txt', '.'),  # ship config next to exe
    ],
    hiddenimports=[
        'modules.analysis',
        'modules.interpretation',
        'modules.output',
        'modules.sampling_utils',
        'modules.input_handler',
        'modules.hypothesis',
        'modules.logger',
        'modules.validation',
        'modules.config',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='htt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='ico.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='htt',
)
