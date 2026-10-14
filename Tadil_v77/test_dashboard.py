import sys,os,tempfile,sqlite3,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;test=Path(tempfile.mkdtemp(prefix='dashboard-',dir=ROOT));os.environ['LOCALAPPDATA']=str(test)
sys.path.insert(0,str(ROOT/'program'));import tadil_app_v77 as m
m.DB.parent.mkdir(parents=True,exist_ok=True)
items=[]
for i,source in enumerate((ROOT.parent/'v76-review/active-original').glob('*.sqlite3')):
 p=m.DB.parent/source.name
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(p) as out:src.backup(out)
 items.append({'id':p.stem,'contractor':'TEST CONTRACTOR '+str(i),'contract':'TEST '+str(i),'project':'TEST PROJECT'})
cat=m.DATA_HOME/'contracts.json';cat.write_text(json.dumps(items),encoding='utf-8')
errors=[];passed=[];apps=[]
for name in ('showinfo','showwarning'):setattr(m.messagebox,name,lambda *a,**kw:None)
m.messagebox.showerror=lambda *a,**kw:errors.append(a)
m.messagebox.askyesno=lambda *a,**kw:True;m.messagebox.askyesnocancel=lambda *a,**kw:True
real_app=m.App
class TrackedApp(real_app):
 def __init__(self):super().__init__();apps.append(self)
m.App=TrackedApp
original_loop=m.tk.Tk.mainloop
answers=[]
from tkinter import simpledialog,filedialog
simpledialog.askstring=lambda *a,**kw:answers.pop(0)
filedialog.askopenfilename=lambda *a,**kw:str(ROOT.parent/'v76-review/active-original/contract_001.sqlite3')
filedialog.asksaveasfilename=lambda *a,**kw:str(test/'chosen backup.sqlite3')
if os.name=='nt':m.tk.Menu.tk_popup=lambda *a,**kw:None # menu actions are invoked separately; native popup tested on X11
def run(root):
 def steps():
  try:
   root.report_callback_exception=lambda *e:errors.append(tuple(str(v) for v in e))
   root.update();canvas=next(w for w in root.winfo_children() if isinstance(w,m.tk.Canvas))
   def xy(x,y):
    sc=min(canvas.winfo_width()/1536,canvas.winfo_height()/1024)
    return round((canvas.winfo_width()-1536*sc)/2+x*sc),round((canvas.winfo_height()-1024*sc)/2+y*sc)
   def event(kind,x,y):
    px,py=xy(x,y);canvas.event_generate(kind,x=px,y=py);root.update()
   def click(x,y):event('<ButtonPress-1>',x,y);event('<ButtonRelease-1>',x,y)
   for x,y in [(450,230),(560,230),(650,230),(1400,230),(380,720),(600,720),(850,720),(1100,720),(1380,720),(120,277),(120,330),(120,380),(120,430),(120,490),(120,540),(120,600)]:
    event('<Motion>',x,y);assert canvas.cget('cursor')=='hand2'
    feedback=canvas.find_withtag('control_feedback');assert len(feedback)==1
    coords=canvas.coords(feedback[0]);assert coords[2]-coords[0]<canvas.winfo_width()*0.34
    assert canvas.itemcget(feedback[0],'outline')!='#ffbb38'
   event('<Motion>',508,720);assert canvas.cget('cursor')=='arrow'
   event('<Motion>',1300,382);assert canvas.cget('cursor')=='arrow'
   passed.append('independent hover areas, no yellow group outline, gaps and empty rows use arrow')
   before=len(apps);event('<ButtonPress-1>',380,720);event('<ButtonRelease-1>',600,720);assert len(apps)==before
   passed.append('drag release outside pressed button does not activate another button')
   for x,y,expected in [(380,720,1),(600,720,2),(850,720,2),(1100,720,4),(1380,720,4),(120,430,3),(120,490,4),(120,600,0),(1370,935,4),(460,447,0)]:
    click(x,y);a=apps[-1];a.update();assert a.nb.index(a.nb.select())==expected
    a.open_contract_manager();root.update();assert root.state()!='withdrawn'
   passed.append('all five stage routes, indices, reports, settings, entry, and edit-contract navigation')
   click(1400,448);a=apps[-1];a.update();assert a.sno.get()==2
   # Registered Tk command must return to existing dashboard, not destroy it.
   def widgets(parent):
    for w in parent.winfo_children():yield w;yield from widgets(w)
   manager=next(w for w in widgets(a) if isinstance(w,(m.ttk.Button,m.tk.Button)) and 'تغییر قرارداد' in w.cget('text'))
   manager.invoke();root.update();assert root.state()!='withdrawn'
   passed.append('new-statement dashboard button creates sequential record; return button reuses dashboard')
   answers.extend(['TEST NEW CONTRACTOR','TEST NEW NUMBER','TEST NEW PROJECT']);click(450,230)
   saved=json.loads(cat.read_text(encoding='utf-8'));assert len(saved)==3
   new=saved[0];bank=m.DB.parent/(new['id']+'.sqlite3');assert bank.exists()
   answers.extend(['TEST EDIT NAME','TEST EDIT NUMBER','TEST EDIT PROJECT']);click(560,230)
   with sqlite3.connect(bank) as c:assert c.execute("select v from settings where k='contractor'").fetchone()[0]=='TEST EDIT NAME'
   click(650,230);assert bank.exists() and len(json.loads(cat.read_text(encoding="utf-8")))==2
   passed.append('add, edit and remove-from-list preserve per-contract database')
   click(120,540);menu=next(w for w in root.winfo_children() if isinstance(w,m.tk.Menu));menu.unpost();menu.invoke(0)
   assert (test/'chosen backup.sqlite3').exists()
   menu.invoke(1);assert len(json.loads(cat.read_text(encoding="utf-8")))==3
   passed.append('backup and legacy recovery copy databases')
   answers.extend(['FOURTH CONTRACTOR','FOURTH NUMBER','FOURTH PROJECT']);click(450,230)
   assert len(json.loads(cat.read_text(encoding='utf-8')))==4
   click(120,277)
   dialog=next(w for w in root.winfo_children() if isinstance(w,m.tk.Toplevel))
   contract_tree=next(w for w in widgets(dialog) if isinstance(w,m.ttk.Treeview))
   assert len(contract_tree.get_children())==4
   contract_tree.selection_set(contract_tree.get_children()[-1])
   choose=next(w for w in widgets(dialog) if isinstance(w,m.ttk.Button));choose.invoke();root.update()
   passed.append('all contracts remain selectable beyond the three dashboard rows')
   assert not errors,errors
  except Exception as e:
   import traceback;traceback.print_exc();errors.append((type(e).__name__,str(e)))
  finally:root.destroy()
 root.after(250,steps);original_loop(root)
m.tk.Tk.mainloop=run;m.start_manager();assert not errors,errors
cat.write_text('{broken',encoding='utf-8');before=cat.read_bytes()
try:m.start_manager();raise AssertionError('corrupt catalog accepted')
except RuntimeError:pass
assert cat.read_bytes()==before;passed.append('corrupt catalog is reported and left intact')
(ROOT/'DASHBOARD_RESULTS.json').write_text(json.dumps({'passed':passed,'errors':errors,'platform':sys.platform},ensure_ascii=False,indent=2),encoding='utf-8')
for name in passed:print('PASS',name)
