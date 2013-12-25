# -*- mode: python -*-

#
# Creates an .exe for the windows spotify version which has no dependencies
#  (ie. python and the python packages are all included)
# To run this script and build you must first install pyinstall and download
# python and all the dependencies. It must be run on windows.

def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)            
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append((f, f, 'DATA'))
    return extra_datas

a = Analysis(['swisher\winbox.py'],
    pathex=['swisher'],
    hiddenimports=[],
    hookspath=None)

a.datas += extra_datas('swisher\\templates')
a.datas += extra_datas('swisher\\assets')
a.datas += extra_datas('swisher\\winresources')
a.datas += extra_datas('mpd-0.17.4-win32')

pyz = PYZ(a.pure)
exe = EXE(pyz,
    a.scripts,
    exclude_binaries=1,
    name=os.path.join('build\\pyi.win32\\swisher', 'swisher.exe'),
    debug=False,
    strip=None,
    upx=True,
    icon='swisher\\winresources\\icon.ico',
    console=False )
coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=None,
    upx=True,
    name=os.path.join('dist', 'swisher'))
