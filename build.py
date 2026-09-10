"""Build the same EXE name on each release; version information lives inside the binary."""
import subprocess
import os
import sys
from pathlib import Path
from version import APP_NAME,VERSION

root=Path(__file__).resolve().parent
# Do not bundle unrelated DLLs from tools injected into the caller's PATH.
build_env=os.environ.copy()
windows=Path(os.environ.get('SystemRoot',r'C:\Windows'))
build_env['PATH']=os.pathsep.join(map(str,[Path(sys.executable).parent,
 Path(sys.base_prefix),Path(sys.base_prefix)/'DLLs',windows/'System32',windows]))
parts=tuple(int(x) for x in VERSION.split('.'))
quad=parts+(0,)*(4-len(parts))
work=root/'build'
work.mkdir(exist_ok=True)
resource=work/'version_info.txt'
resource.write_text(f'''VSVersionInfo(
 ffi=FixedFileInfo(filevers={quad!r},prodvers={quad!r},mask=0x3f,flags=0,OS=0x40004,fileType=0x1,subtype=0,date=(0,0)),
 kids=[StringFileInfo([StringTable('040904B0',[
  StringStruct('CompanyName','Lenny'), StringStruct('FileDescription',{APP_NAME!r}),
  StringStruct('FileVersion',{VERSION!r}), StringStruct('ProductVersion',{VERSION!r}),
  StringStruct('ProductName',{APP_NAME!r}), StringStruct('OriginalFilename','LennyTorrentDownloader.exe')
 ])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])''','utf-8')
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
 '--name','LennyTorrentDownloader','--icon',str(root/'assets'/'logo.png'),
 '--add-data',f'{root / "assets"};assets','--version-file',str(resource),
 '--exclude-module','imageio_ffmpeg','--exclude-module','unittest',
 '--distpath',str(root/'dist'),'--workpath',str(work/'pyinstaller'),
 '--specpath',str(work),str(root/'app.py')],cwd=root,env=build_env,check=True)
print('Built:',root/'dist'/'LennyTorrentDownloader.exe')
