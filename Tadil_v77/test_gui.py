import os,sys,tempfile,sqlite3,shutil,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TEST=Path(tempfile.mkdtemp(prefix='gui-',dir=ROOT));os.environ['LOCALAPPDATA']=str(TEST)
sys.path.insert(0,str(ROOT/'program'))
import tadil_app_v77 as m
errors=[];notes=[]
for name in ['showinfo','showwarning']:setattr(m.messagebox,name,lambda *a,**k:notes.append(a))
m.messagebox.showerror=lambda *a,**k:errors.append(a)
m.messagebox.askyesno=lambda *a,**k:True
m.messagebox.askyesnocancel=lambda *a,**k:True
m.DB.parent.mkdir(parents=True,exist_ok=True)
source=ROOT.parent/'v76-review/active-original/contract_001.sqlite3'
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(m.DB) as dest:src.backup(dest)
a=m.App();a.report_callback_exception=lambda *exc:errors.append(tuple(str(x) for x in exc));a.update()
original_rows=len(a.tree.get_children());assert original_rows==48
# Actual Tk variable and database metadata roundtrip.
a.vars['project'].set('GUI TEST PROJECT');a.save_settings();a.update()
# Edit real overlay Entry, then save with partial dates.
a.nb.select(a.tstmt);a.update();row=a.tree.get_children()[0]
a.edit_cell(row,'#4');a.update();entries=[w for w in a.tree.winfo_children() if isinstance(w,m.ttk.Entry)];assert entries
entries[-1].delete(0,'end');entries[-1].insert(0,'777777');a.ss.set('');a.se.set('');a.save_stmt();a.update()
key=a.tree.set(row,'key');assert a.c.execute('select current from amounts where stmt=1 and itemkey=?',(key,)).fetchone()[0]==777777
# Both shared Spinbox routes are traced; immediate save also resolves pending transition.
a.sno.set(2);a.save_stmt();a.update();assert a._loaded_statement_no==2
assert a.c.execute('select count(*) from selected where stmt=2').fetchone()[0]==48
assert a.tree.set(a.tree.get_children()[0],'prev')=='777777'
# Actual new-statement button command.
newbutton=[]
def allwidgets(parent):
 for w in parent.winfo_children():
  yield w;yield from allwidgets(w)
for w in allwidgets(a):
 if isinstance(w,m.ttk.Button) and 'صورت وضعیت جدید' in w.cget('text'):newbutton.append(w)
assert len(newbutton)==1;newbutton[0].invoke();a.update();assert a.sno.get()==3
# Load/save chapter checks with concrete widgets and DB.
a.nb.select(a.tsel);a.select_all_chapters();a.save_selection();a.update();a.clear_all_chapters();a.load_selection();a.update()
# Restore original date range for meaningful calculations (unchanged formula).
with sqlite3.connect(source) as c:dates=c.execute('select start,end,sdate from statements where no=1').fetchone()
a.ss.set(dates[0]);a.se.set(dates[1]);a.sd.set(dates[2]);rows=a.calculate();assert rows
# Existing print paths exercised; opening external viewers is stubbed.
opened=[];a.open_file=lambda p:opened.append(Path(p));a.print_calc();a.print_cover();a.load_indices();a.audit_indices_ui()
assert len(opened)==2 and all(p.is_file() and '@page' in p.read_text(encoding='utf-8') and 'A4' in p.read_text(encoding='utf-8') for p in opened)
# All nav buttons change active tab and active styling.
for index,b in enumerate(a.nav_buttons):
 b.invoke();a.update();assert a.nb.index(a.nb.select())==index;assert b.cget('relief')=='sunken'
assert not errors,errors
saved_number=a.sno.get();a._close_safely()
b=m.App();b.update();assert b.vars['project'].get()=='GUI TEST PROJECT';assert b.sno.get()==saved_number;assert len(b.ct.get_children())==len(rows);b._close_safely()
assert not errors,errors
print('PASS real Tk GUI: init, metadata, amount editor, draft save, number switch, new statement, chapter controls, calculation, A4 HTML outputs, five nav buttons, close and reopen')
(ROOT/'GUI_RESULTS.json').write_text(json.dumps({'passed':True,'errors':errors,'environment':sys.platform,'scope':'Actual Tk widgets; dialogs auto-answered; HTML validated but physical print not tested','test_directory':str(TEST)},ensure_ascii=False,indent=2))
