# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/monitor/littletiles-obj-tool/src/littletiles_obj_tool/desktop.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/monitor/littletiles-obj-tool/src/littletiles_obj_tool/templates', 'templates'), ('/home/monitor/littletiles-obj-tool/src/littletiles_obj_tool/static', 'static')],
    hiddenimports=[],
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
    name='LittleTilesOBJTool',
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
)
