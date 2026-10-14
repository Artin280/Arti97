import os,sys,tempfile,types,sqlite3,importlib.util,json,subprocess
from pathlib import Path
ROOT=Path('/workspace/v78');testroot=Path(tempfile.mkdtemp(prefix='regression-',dir=ROOT));os.environ['LOCALAPPDATA']=str(testroot)
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 for action in ['showinfo','showerror','showwarning']:setattr(m.messagebox,action,lambda *a,**k:None)
 return m
v78=module('v78',ROOT/'program/tadil_app_v78.py');v76=module('v76',Path('/workspace/v76-review/source/payload/tadil_app_v76.py'))
class V:
 def __init__(self,v=''):self.v=v
 def get(self):return self.v
 def set(self,v):self.v=v
class Tree:
 columns=('key','field','ch','desc','cur','prev')
 def __init__(self):self.rows={}
 def get_children(self):return tuple(self.rows)
 def delete(self,key):del self.rows[key]
 def insert(self,*a,**kw):
  key=kw.get('iid',str(len(self.rows)+1));self.rows[key]=dict(zip(self.columns,kw['values']));return key
 def set(self,i,col,value=None):
  if value is None:return self.rows[i][col]
  self.rows[i][col]=value
class AppFake:
 def after_cancel(self,*a):pass
 def after(self,*a):return None
 def focus_get(self):return None
 def winfo_exists(self):return True
 def _save_unsaved_settings(self):pass
 def load_selection(self):pass
 def _base_year(self):return 1397
 def bind_methods(self,m):
  for name in ['load_stmt','prev','_restore_calc_snapshot','_finish_amount_edit','_save_active_statement_if_valid','_invalidate_calculations','_switch_statement','_ensure_active_statement','save_stmt_silent','validate_stmt_dates','idx','calculate']:
   if hasattr(m.App,name):setattr(self,name,types.MethodType(getattr(m.App,name),self))
def fixture(m,source,tag):
 a=AppFake();p=testroot/(tag+'.sqlite3')
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as c,sqlite3.connect(p) as out:c.backup(out)
 a.c=sqlite3.connect(p);a.c.row_factory=sqlite3.Row;a.sno=V(1);a.ss=V();a.se=V();a.sd=V();a.e_start=a.ss;a.e_end=a.se;a.e_sdate=a.sd
 a.tree=Tree();a.ct=Tree();a.total=V();a.vars={k:V(v) for k,v in a.c.execute('select k,v from settings')};a.bind_methods(m)
 a._switching_statement=False;a._statement_switch_job=None;a._amount_editor=None;a._loaded_statement_no=1
 a.load_stmt();return a,p
results=[]
def check(name,cond):
 assert cond,name
 results.append(name);print('PASS',name)
source=Path('/workspace/v76-review/active-original/contract_001.sqlite3')
a,p=fixture(v78,source,'draft')
key=a.tree.get_children()[0];itemkey=a.tree.set(key,'key');a.tree.set(key,'cur','987654');a.ss.set('');a.se.set('');a._save_active_statement_if_valid();a.c.close()
code="import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); assert c.execute('select current from amounts where stmt=1 and itemkey=?',(sys.argv[2],)).fetchone()[0]==987654; assert c.execute('select start,end from statements where no=1').fetchone()==('','')"
subprocess.run([sys.executable,'-c',code,str(p),itemkey],check=True)
check('blank draft dates and amount survive separate process reopen',True)
a,p=fixture(v78,source,'switch');key=a.tree.get_children()[0];itemkey=a.tree.set(key,'key');a.tree.set(key,'cur','765432');a.sno.set(2);a._switch_statement()
check('switch saves old statement under old number',a.c.execute('select current from amounts where stmt=1 and itemkey=?',(itemkey,)).fetchone()[0]==765432)
a._save_active_statement_if_valid()
check('new statement persists inherited chapters',a.c.execute('select count(*) from selected where stmt=2').fetchone()[0]==48)
check('new amount starts at zero',a.c.execute('select current from amounts where stmt=2 and itemkey=?',(itemkey,)).fetchone()[0]==0)
check('previous amount follows saved prior statement',a.prev(2,itemkey)==765432)
a.c.close()
for source in Path('/workspace/v76-review/active-original').glob('*.sqlite3'):
 old,_=fixture(v76,source,source.stem+'old');new,p=fixture(v78,source,source.stem+'new')
 rows_old=old.calculate();rows_new=new.calculate()
 check(source.stem+' unchanged calculation rows compared with v76',bool(rows_new) and rows_old==rows_new)
 check(source.stem+' unchanged calculation totals',old.field_totals==new.field_totals)
 new.c.close();new.c=sqlite3.connect(p);new.c.row_factory=sqlite3.Row;new.load_stmt()
 check(source.stem+' calculation snapshot restored after reconnect',len(new.ct.get_children())==len(rows_new))
 key=new.tree.get_children()[0];new.tree.set(key,'cur',str(float(new.tree.set(key,'cur'))+1));new._save_active_statement_if_valid()
 check(source.stem+' edited amount invalidates snapshot',new.c.execute('select count(*) from calculation_snapshots').fetchone()[0]==0)
 check(source.stem+' test database integrity',new.c.execute('pragma integrity_check').fetchone()[0]=='ok')
 old.c.close();new.c.close()
(ROOT/'TEST_RESULTS.json').write_text(json.dumps({'passed':results,'scope':'Headless tests with real SQLite and lightweight widget substitutes; Windows GUI not tested','test_directory':str(testroot)},ensure_ascii=False,indent=2))
