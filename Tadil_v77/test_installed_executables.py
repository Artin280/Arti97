import os,sys,json,sqlite3,tempfile,subprocess,hashlib,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=Path(tempfile.mkdtemp(prefix='end-to-end-',dir=ROOT));profile=base/'profile with spaces';profile.mkdir();desktop=base/'desktop';desktop.mkdir()
os.environ['LOCALAPPDATA']=str(profile)
data=profile/'TadilApp/data';(data/'contracts').mkdir(parents=True)
for source in (ROOT.parent/'v76-review/active-original').glob('*.sqlite3'):
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(data/'contracts'/source.name) as out:src.backup(out)
(data/'contracts.json').write_bytes((ROOT.parent/'v76-review/data-original/contracts.json').read_bytes())
def hashes():return {str(p.relative_to(data)):hashlib.sha256(p.read_bytes()).hexdigest() for p in data.rglob('*') if p.is_file()}
before=hashes();keys=[]
try:
 for keyname,typ in [('Shell Folders',winreg.REG_SZ),('User Shell Folders',winreg.REG_EXPAND_SZ)]:
  path='Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'+keyname
  with winreg.CreateKey(winreg.HKEY_CURRENT_USER,path) as key:
   try:old=winreg.QueryValueEx(key,'Desktop')
   except FileNotFoundError:old=None
   keys.append((path,old));winreg.SetValueEx(key,'Desktop',0,typ,str(desktop))
 installer=ROOT/'dist/Setup_Tadil_v77.exe'
 subprocess.run([str(installer),'--quiet'],check=True,timeout=180)
 assert hashes()==before
 record=json.loads((profile/'TadilApp/installed_v77.json').read_text(encoding='utf-8'))
 assert Path(record['shortcut']).exists()
 exe=Path(record['program'])/'Tadil_v77.exe';qa=base/'synthetic-data'
 subprocess.run([str(exe),'--smoke-test',str(qa)],check=True,timeout=90)
 assert json.loads((qa/'results.json').read_text(encoding='utf-8'))['ok']
 subprocess.run([str(exe),'--verify-saved-smoke',str(qa)],check=True,timeout=90)
 assert json.loads((qa/'verified.json').read_text(encoding='utf-8'))['ok']
 assert hashes()==before
 subprocess.run([str(installer),'--quiet'],check=True,timeout=180)
 assert hashes()==before
 record2=json.loads((profile/'TadilApp/installed_v77.json').read_text(encoding='utf-8'))
 assert record2['backup']!=record['backup']
 for b in (profile/'TadilApp/installer_backups').glob('v77_*'):
  for p in (b/'data/contracts').glob('*.sqlite3'):
   with sqlite3.connect(p) as c:assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
 result={'ok':True,'platform':sys.platform,'runtime':'Wine 10.0, not native Windows','tests':['packaged installer first install','real Windows shell-link creation','installed executable starts and exercises GUI','separate process restores saved metadata, dates, amounts and calculation snapshot','packaged installer reinstall','original test data hashes unchanged','SQLite backup integrity'], 'test_directory':str(base)}
 (ROOT/'END_TO_END_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('PASS packaged installer, installed app, separate-process reopen and reinstall preserve data')
finally:
 for path,old in keys:
  with winreg.OpenKey(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_SET_VALUE) as key:
   if old is None:winreg.DeleteValue(key,'Desktop')
   else:winreg.SetValueEx(key,'Desktop',0,old[1],old[0])
