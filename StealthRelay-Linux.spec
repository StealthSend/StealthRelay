# -*- mode: python -*-
a = Analysis(['Python/stealthrelay.py'],
             pathex=['/home/jstroud/GitHub/stealth/StealthRelay'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='StealthRelay',
          debug=False,
          strip=None,
          upx=True,
          console=True )
