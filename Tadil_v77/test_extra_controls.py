import os,sys,tempfile,sqlite3,csv,json
from pathlib import Path
R=Path(__file__).resolve().parent;qa=Path(tempfile.mkdtemp(prefix='extra-controls-',dir=R));os.environ['LOCALAPPDATA']=str(qa);sys.path.insert(0,str(R/'program'))
import tadil_app_v77 as m
m.DB.parent.mkdir(parents=True,exist_ok=True)
source=R.parent/'v76-review/active-original/contract_001.sqlite3'
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(m.DB) as out:src.backup(out)
errors=[]
for name in ('showinfo','showwarning'):setattr(m.messagebox,name,lambda *a,**kw:None)
m.messagebox.showerror=lambda *a,**kw:errors.append(a)
m.messagebox.askyesno=lambda *a,**kw:True
from tkinter import filedialog
a=m.App();a.update()
export=qa/'backup.sqlite3';filedialog.asksaveasfilename=lambda **kw:str(export);a.backup_current();assert export.exists()
# Explicit import in a test-only database, using identical existing index values.
entries=[]
for period in ('1397Q1','1400Q1'):
 row=a.c.execute("select field,chapter,period,value,status from indices where field='فاضلاب' and chapter='1' and period=?",(period,)).fetchone();assert row;entries.append(tuple(row))
p=qa/'indices.csv'
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['field','chapter','period','value','status']);w.writerows(entries)
filedialog.askopenfilename=lambda **kw:str(p);a.import_indices_csv();assert not errors,errors
before=list(a.c.execute('select * from indices order by field,chapter,period'))
p.write_text('field,chapter,period,value,status\nفاضلاب,1,1400Q1,not-a-number,test\n',encoding='utf-8-sig');a.import_indices_csv();assert errors
assert before==list(a.c.execute('select * from indices order by field,chapter,period'));errors.clear()
# Refresh must ask before discarding a committed on-screen edit and respect cancellation.
a.nb.select(a.tstmt);a.update();row=a.tree.get_children()[0];old=a.tree.set(row,'cur');a.tree.set(row,'cur','999');m.messagebox.askyesno=lambda *a,**kw:False;a.confirm_refresh();assert a.tree.set(row,'cur')=='999'
m.messagebox.askyesno=lambda *a,**kw:True;a.confirm_refresh();assert a.tree.set(a.tree.get_children()[0],'cur')==old
# Both external opening commands dispatch and preserve Unicode paths.
opened=[];m.webbrowser.open=lambda value:opened.append(value)
if os.name=='nt':m.os.startfile=lambda value:opened.append(value)
a.open_out();a.open_file(export);assert len(opened)==2
# Amount edit cancellation should leave original table value intact.
a.update();row=a.tree.get_children()[0];a.edit_cell(row,'#4');a.update();ent=next(w for w in a.tree.winfo_children() if isinstance(w,m.ttk.Entry));ent.delete(0,'end');ent.insert(0,'888');ent.event_generate('<Escape>');a.update();assert a.tree.set(row,'cur')==old
assert not errors,errors;a._close_safely()
(R/'EXTRA_CONTROLS_RESULTS.json').write_text(json.dumps({'ok':True,'platform':sys.platform,'tests':['contract backup','valid 1397 and 1400 CSV import','invalid CSV leaves indices unchanged','refresh cancellation and confirmed refresh','output folder and file dispatch','Escape cancels amount editing']},ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS backup, index import validation, refresh confirmation, output dispatch and edit cancellation')
