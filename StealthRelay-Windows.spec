# -*- mode: python -*-
a = Analysis(['Python\\stealthrelay.py'],
             pathex=['d:\\StealthRelay'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='StealthRelay.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True , icon='Resources\\StealthCoin.ico')
