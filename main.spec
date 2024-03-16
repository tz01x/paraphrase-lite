# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['script.py'],
    pathex=[],
    binaries=[],
    datas=[('paraphrase_lite', 'paraphrase_lite')],
    hiddenimports=['requests', 'cryptography.fernet', 'hugchat', 'hugchat.hugchat', 'hugchat.login'],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
