exec(open('/workspace/v77/test_regression.py').read().split('results=[]')[0])
source=Path('/workspace/v76-review/active-original/contract_001.sqlite3')
a,p=fixture(v77,source,'chapters');a.selvars={('فاضلاب','19'):V(True)};a.equip=V(False);a.nb=types.SimpleNamespace(select=lambda *x:None);a.tstmt=None
for name in ['_save_screen_amounts','save_selection']:
 setattr(a,name,types.MethodType(getattr(v77.App,name),a))
key=a.tree.get_children()[0];itemkey=a.tree.set(key,'key');saved=a.c.execute('select current from amounts where stmt=1 and itemkey=?',(itemkey,)).fetchone()[0];a.tree.set(key,'cur','543210')
v77.messagebox.askyesnocancel=lambda *args,**kwargs:None
before='\n'.join(a.c.iterdump());a.save_selection();assert before=='\n'.join(a.c.iterdump());print('PASS cancellation leaves database unchanged')
v77.messagebox.askyesnocancel=lambda *args,**kwargs:True
a.ss.set('1404/01');a.sd.set('1404/02/03')
before_count=a.c.execute('select count(*) from selected where stmt=1').fetchone()[0];a.save_selection()
assert a.c.execute('select count(*) from selected where stmt=1').fetchone()[0]==before_count+1
assert a.c.execute('select current from amounts where stmt=1 and itemkey=?',(itemkey,)).fetchone()[0]==543210
print('PASS adding a chapter retains existing chapters and amount')
assert a.ss.get()=='1404/01' and a.sd.get()=='1404/02/03'
print('PASS chapter addition preserves partial and presentation dates')
a.c.close()
for source in Path('/workspace/v76-review/active-original').glob('*.sqlite3'):
 a,p=fixture(v77,source,source.stem+'metadata');a.contract_db_path=p
 a._settings_values=lambda:{k:v.get().strip() for k,v in a.vars.items()}
 a.vars['project'].set('TEST METADATA REOPEN')
 a._persist_settings=types.MethodType(v77.App._persist_settings,a);a._persist_settings();a.c.close()
 with sqlite3.connect(p) as c:assert c.execute("select v from settings where k='project'").fetchone()[0]=='TEST METADATA REOPEN'
 print('PASS contract metadata save and reopen',source.stem)
