import sys,subprocess,json,hashlib,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent
kind=sys.argv[1]
common=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--version-file',str(root/'version_info.txt'),'--distpath',str(root/'dist'),'--workpath',str(root/'pyinstaller-build'/kind),'--specpath',str(root/'specs')]
if kind=='app':
 subprocess.run(common+['--onedir','--name','Tadil_v77','--paths',str(root/'program'),'--add-data',str(root/'program/assets')+';assets','--add-data',str(root/'program/licenses')+';licenses',str(root/'program/Tadil.pyw')],check=True)
 app=root/'dist/Tadil_v77';payload=root/'installer/application.zip';files={};size=0
 with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for p in sorted(app.rglob('*')):
   if p.is_file():
    name=p.relative_to(app).as_posix();content=p.read_bytes();files[name]=hashlib.sha256(content).hexdigest();size+=len(content);out.writestr(name,content)
 (root/'installer/manifest.json').write_text(json.dumps({'version':77,'payload_sha256':hashlib.sha256(payload.read_bytes()).hexdigest(),'unpacked_bytes':size,'files':files},indent=2),encoding='utf-8')
 print('APP_PAYLOAD_READY',len(files),size)
elif kind=='installer':
 subprocess.run(common+['--onefile','--name','Setup_Tadil_v77','--paths',str(root/'installer'),'--add-data',str(root/'installer/application.zip')+';.', '--add-data',str(root/'installer/manifest.json')+';.',str(root/'installer/installer.py')],check=True)
 print('INSTALLER_READY',root/'dist/Setup_Tadil_v77.exe')
else:raise ValueError(kind)
