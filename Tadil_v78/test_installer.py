import sys,os,tempfile,sqlite3,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'installer'));import installer as m
base=Path(tempfile.mkdtemp(prefix='installer-',dir=root))/'آزمون نصب with spaces';base.mkdir(parents=True)
data=base/'data';(data/'contracts').mkdir(parents=True)
for source in (root.parent/'v76-review/active-original').glob('*.sqlite3'):
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(data/'contracts'/source.name) as out:src.backup(out)
(data/'contracts.json').write_text((root.parent/'v76-review/data-original/contracts.json').read_text(encoding='utf-8'),encoding='utf-8')
(base/'program_v76').mkdir();(base/'program_v76/previous-program.txt').write_text('OLD PROGRAM PRESERVE')
before={str(p.relative_to(data)):m.digest(p) for p in data.rglob('*') if p.is_file()}
shortcut=base/'desktop'/'Tadil v78.lnk'
if os.name!='nt':
 m.create_shortcut=lambda path,target:(Path(path).parent.mkdir(parents=True,exist_ok=True),Path(path).write_text(str(target)))
result=m.install(base,shortcut)
assert before=={str(p.relative_to(data)):m.digest(p) for p in data.rglob('*') if p.is_file()}
assert shortcut.exists() and (base/'program_v78/Tadil_v78.exe').exists()
for p in (Path(result['backup'])/'data/contracts').glob('*.sqlite3'):
 with sqlite3.connect(p) as c:assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
assert (Path(result['backup'])/'program_v76/previous-program.txt').read_text()=='OLD PROGRAM PRESERVE'
print('PASS first install preserves data, verifies SQLite backups and retains v76')
result2=m.install(base,shortcut)
assert before=={str(p.relative_to(data)):m.digest(p) for p in data.rglob('*') if p.is_file()}
assert Path(result2['backup'])!=Path(result['backup'])
assert (Path(result2['backup'])/'program_v78_replaced/Tadil_v78.exe').exists()
print('PASS reinstall preserves data and creates a distinct full backup')
with m.RuntimeLock(base):
 try:m.install(base,shortcut);raise AssertionError('lock ignored')
 except RuntimeError as exc:assert 'نصب‌کننده' in str(exc)
print('PASS concurrent application/install lock prevents replacement')
old=m.digest(base/'program_v78/Tadil_v78.exe');oldshortcut=shortcut.read_bytes();oldfunc=m.create_shortcut
m.create_shortcut=lambda *a:(_ for _ in ()).throw(OSError('SIMULATED SHORTCUT FAILURE'))
try:m.install(base,shortcut);raise AssertionError('failure not propagated')
except OSError:pass
assert m.digest(base/'program_v78/Tadil_v78.exe')==old and shortcut.read_bytes()==oldshortcut
assert before=={str(p.relative_to(data)):m.digest(p) for p in data.rglob('*') if p.is_file()}
m.create_shortcut=oldfunc
print('PASS installation failure rolls back program and shortcut without modifying data')
manifest=json.loads((m.BUNDLE/'manifest.json').read_text());manifest['payload_sha256']='0'*64
try:m.validate_payload(m.BUNDLE/'application.zip',manifest);raise AssertionError('invalid digest accepted')
except RuntimeError:pass
print('PASS damaged payload rejected before installation')
(root/('INSTALLER_RESULTS_WINDOWS.json' if os.name=='nt' else 'INSTALLER_RESULTS_LINUX.json')).write_text(json.dumps({'ok':True,'platform':sys.platform,'test_directory':str(base),'installation':result2},ensure_ascii=False,indent=2),encoding='utf-8')
