import sys,os,tempfile,sqlite3,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
stage=sys.argv[1] if len(sys.argv)>1 else 'write'
QA=Path(sys.argv[2]) if len(sys.argv)>2 else Path(tempfile.mkdtemp(prefix='dashboard-roundtrip-',dir=ROOT))
os.environ['LOCALAPPDATA']=str(QA);sys.path.insert(0,str(ROOT/'program'))
import tadil_app_v78 as m
from tkinter import ttk
errors=[];apps=[]
for name in ('showinfo','showwarning'):setattr(m.messagebox,name,lambda *a,**kw:None)
m.messagebox.showerror=lambda *a,**kw:errors.append(a)
m.messagebox.askyesno=lambda *a,**kw:True;m.messagebox.askyesnocancel=lambda *a,**kw:True
if stage=='write':
 m.DB.parent.mkdir(parents=True,exist_ok=True)
 items=[]
 for i in (1,2):
  m.DB=m.DATA_HOME/'contracts'/('test_contract_'+str(i)+'.sqlite3')
  with m.db() as c:
   for key,value in [('contractor','TEST CONTRACTOR '+str(i)),('contract_no',str(1000+i)),('project','TEST PROJECT '+str(i)),('employer','EMPLOYER '+str(i)),('consultant','CONSULTANT '+str(i)),('supervisor','SUPERVISOR '+str(i))]:c.execute('insert or replace into settings values(?,?)',(key,value))
   for no in (8,9,10):
    c.execute("insert into selected values(?,'فاضلاب','1','TEST')",(no,))
    c.execute("insert into amounts values(?,'فاضلاب|1',?)",(no,10000+no))
    c.execute('insert into statements values(?,?,?,?)',(no,'1397/01/01','1397/01/31','1397/02/01'))
  items.append({'id':m.DB.stem,'contractor':'TEST CONTRACTOR '+str(i),'contract':str(1000+i),'project':'TEST PROJECT '+str(i)})
 (m.DATA_HOME/'contracts.json').write_text(json.dumps(items),encoding='utf-8')
real=m.App
class TrackingApp(real):
 def __init__(self):super().__init__();apps.append(self)
m.App=TrackingApp
loop=m.tk.Tk.mainloop

def widgets(parent):
 for w in parent.winfo_children():yield w;yield from widgets(w)
def driver(root):
 def run():
  try:
   root.report_callback_exception=lambda *e:errors.append(tuple(str(v) for v in e))
   root.update();canvas=next(w for w in root.winfo_children() if isinstance(w,m.tk.Canvas))
   def click(x,y):
    sc=min(canvas.winfo_width()/1536,canvas.winfo_height()/1024);px=round((canvas.winfo_width()-1536*sc)/2+x*sc);py=round((canvas.winfo_height()-1024*sc)/2+y*sc)
    canvas.event_generate('<ButtonPress-1>',x=px,y=py);canvas.event_generate('<ButtonRelease-1>',x=px,y=py);root.update()
   searches=[w for w in root.winfo_children() if isinstance(w,m.tk.Entry)];assert len(searches)==2
   assert searches[0].winfo_x()+searches[0].winfo_width()<searches[1].winfo_x()
   if stage=='write':
    searches[0].insert(0,'TEST CONTRACTOR 2');searches[1].insert(0,'۱۰۰۲');root.update()
    click(1450,450);a=apps[-1];assert a.contract_db_path.stem=='test_contract_2';a.open_contract_manager();root.update()
    for search in searches:search.delete(0,'end')
   click(120,277)
   dialog=next(w for w in root.winfo_children() if isinstance(w,m.tk.Toplevel));tree=next(w for w in widgets(dialog) if isinstance(w,ttk.Treeview))
   assert tree.exists('c0s8') and tree.exists('c0s9') and tree.exists('c0s10')
   # Explicit target: old statement 8 despite latest number 10.
   tree.selection_set('c0s8');button=next(w for w in widgets(dialog) if isinstance(w,ttk.Button));button.invoke();root.update()
   a=apps[-1];a.report_callback_exception=lambda *e:errors.append(tuple(str(v) for v in e));a.update();assert a.sno.get()==8
   assert all(v._tk is a.tk for v in [*a.vars.values(),a.ss,a.se,a.sd,a.sno,a.total,*a.selvars.values(),a.equip])
   def field(key):return next(w for w in widgets(a.tset) if isinstance(w,ttk.Entry) and str(w.cget('textvariable'))==str(a.vars[key]))
   def set_text(widget,value):widget.delete(0,'end');widget.insert(0,value)
   if stage=='write':
    for key,val in [('project','UI TYPED PROJECT'),('contract_no','9008'),('employer','UI EMPLOYER'),('consultant','UI CONSULTANT'),('supervisor','UI SUPERVISOR')]:set_text(field(key),val)
    # Exercise genuine widget editing, not StringVar.set.
    a.nb.select(a.tstmt);a.update()
    for entry,value in [(a.e_start,'1397/02/01'),(a.e_end,'1397/02/31'),(a.e_sdate,'1397/03/02')]:set_text(entry,value)
    row=a.tree.get_children()[0];a.edit_cell(row,'#4');a.update();editor=next(w for w in a.tree.winfo_children() if isinstance(w,ttk.Entry));set_text(editor,'88000');a.save_stmt();a.update()
    rows=a.calculate();assert rows
    total=a.total.get();assert a.tk.globalgetvar(str(a.total))==total
    (QA/'expected.json').write_text(json.dumps({'total':total,'rows':rows}),encoding='utf-8')
   else:
    assert field('project').get()=='UI TYPED PROJECT' and field('contract_no').get()=='9008'
    assert field('employer').get()=='UI EMPLOYER' and field('consultant').get()=='UI CONSULTANT' and field('supervisor').get()=='UI SUPERVISOR'
    assert a.e_start.get()=='1397/02/01' and a.e_end.get()=='1397/02/31' and a.e_sdate.get()=='1397/03/02'
    assert a.tree.set(a.tree.get_children()[0],'cur')=='88000'
    expected=json.loads((QA/'expected.json').read_text(encoding='utf-8'));assert len(a.ct.get_children())==len(expected['rows']) and a.total.get()==expected['total']
    assert a.c.execute('select current from amounts where stmt=10').fetchone()[0]==10010
   a.open_contract_manager();root.update()
   # Closing the real dashboard terminates the whole UI.
   root.destroy()
  except Exception as exc:
   import traceback;traceback.print_exc();errors.append((type(exc).__name__,str(exc)));root.destroy()
 root.after(250,run);loop(root)
m.tk.Tk.mainloop=driver;m.start_manager();assert not errors,errors
if stage=='write':
 command=[sys.executable,'--dashboard-smoke-read',str(QA)] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).resolve()),'read',str(QA)]
 subprocess.run(command,check=True,env=os.environ)
 (QA/'DASHBOARD_PERSISTENCE_RESULTS.json').write_text(json.dumps({'ok':True,'platform':sys.platform,'test_directory':str(QA),'scope':'real dashboard -> hierarchy -> statement 8; genuine Entry editing; full process exit; new process reads all visible values, amounts and snapshots; independent name/contract-number search'},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS v78 dashboard',stage,'real Entry state, statement target and full-process persistence')
